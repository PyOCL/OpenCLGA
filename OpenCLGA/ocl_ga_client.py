#!/usr/bin/python3
import traceback
import argparse
import pickle
import pyopencl as cl
from pyopencl import device_info as di
import random
import tempfile
import time
import uuid
from multiprocessing import Process, Pipe, Value, Event

from .ocl_ga import OpenCLGA
from .utilities.generaltaskthread import Logger
from .utilities.socketserverclient import Client, OP_MSG_BEGIN, OP_MSG_END

oclClient = None

def query_devices(c_p):
    import pyopencl as cl
    platforms = cl.get_platforms()
    devices = platforms[0].get_devices()

    data = []
    for pidx in range(len(platforms)):
            devices = platforms[pidx].get_devices()
            for didx in range(len(devices)):
                data.append((pidx, didx))
    c_p.send(data)

class OpenCLGAWorker(Process, Logger):
    def __init__(self, platform_index, device_index, ip, port):
        Process.__init__(self)
        Logger.__init__(self)
        self.daemon = True
        self.exit_evt = Event()
        self.running = Value('i', 0)
        self.platform_index = platform_index
        self.device_index = device_index
        self.ip = ip
        self.port = port
        self.uuid = uuid.uuid1().hex

    def terminate(self):
        self.exit_evt.set()
        while self.running.value:
            time.sleep(0.1)
        super(OpenCLGAWorker, self).terminate()

    def run(self):
        self.running.value = 1
        random.seed()
        try:
            self.__create_context()
            self.info("Worker created for context {}".format(self.device.name))
            self.info("Worker [{0}] connect to server {1}:{2}".format(
                                self.device.name, self.ip, self.port))
        except:
            self.error("Create OpenCL context failed !")
            return
        try:
            self.client = Client(self.ip, self.port, {0 : { "pre" : OP_MSG_BEGIN,
                                                            "post": OP_MSG_END,
                                                            "callback" : self._process_data}})
            self.__notify_client_online()
        except ConnectionRefusedError:
            self.error("Connection refused! Please check Server status.")
            self.client = None
            return

        self.info("Worker [{0}] wait for commands".format(self.device.name))
        try:
            # If client is terminated by ctrl+c, exception will be caught in
            # worker process.
            self.exit_evt.wait()
        except KeyboardInterrupt:
            pass
        finally:
            self.__shutdown()

    def __create_context(self):
        self.platform = cl.get_platforms()[self.platform_index]
        assert self.platform is not None
        self.device = self.platform.get_devices()[self.device_index]
        assert self.device is not None
        self.dev_type = self.device.get_info(di.TYPE)
        self.context = cl.Context(devices=[self.device])
        return self.context

    def __send_and_dump_info(self, index, data):
        self.verbose("{0}\t\t==> {1} ~ {2} ~ {3}".format(index, data["best"], data["avg"],
                                                                data["worst"]))
        self.__send({"type": "generation_result",
                     "index": index,
                     "result": data})

    def _run_end(self):
        self.__send({"type": "end"})

    def __create_ocl_ga(self, options):
        options["cl_context"] = self.context
        options["generation_callback"] = self.__send_and_dump_info
        self.ocl_ga = OpenCLGA(options, action_callbacks={'run' : self._run_end})
        self.ocl_ga.prepare()
        self.info("Worker [{}]: oclGA prepared".format(self.device.name))

    def _process_data(self, data):
        '''
        Called when data is received from server.
        '''
        # Conver bytearray "data" to string-like object
        msg = str(data, 'ASCII')
        dict_msg = eval(msg)
        cmd = dict_msg["command"]
        payload = dict_msg["data"]
        self.verbose("Worker [{}]: cmd received = {}".format(self.device.name, cmd))

        if cmd in ["pause", "stop", "restore", "best", "save", "statistics"] and not self.ocl_ga:
            self.error("Cmd '{}' will only be processed after prepared ".format(cmd))
            return
        try:
            if cmd == "prepare":
                self.__create_ocl_ga(pickle.loads(payload))
            elif cmd == "pause":
                self.ocl_ga.pause()
            elif cmd == "stop":
                self.ocl_ga.stop()
            elif cmd == "restore":
                self.ocl_ga.restore(payload)
            elif cmd == "save":
                # NOTE : Need to think about this ... too large !
                # state_file = tempfile.NamedTemporaryFile(delete=False)
                self.ocl_ga.save(payload)
                # saved_filename  = state_file.name
                # with open(state_file.name, 'rb') as fd:
                self.__send({"type": "save",
                             "result": None})
                # state_file.close()
            elif cmd == "best":
                # TODO : A workaround to get best chromesome back for TSP
                #       May need to pickle this tuple as it contains specific data structure.
                best_chromosome, best_fitness, chromesome_kernel = self.ocl_ga.get_the_best()
                self.__send({"type": "best",
                             "result": repr(best_chromosome)})
            elif cmd == "statistics":
                self.__send({"type": "statistics",
                             "result": self.ocl_ga.get_statistics()})
            elif cmd == "run":
                prob_mutate, prob_cross = payload
                self.info("Worker [{}]: oclGA run with {}/{}".format(self.device.name,
                                                                            prob_mutate, prob_cross))
                self.ocl_ga.run(prob_mutate, prob_cross)
            elif cmd == "exit":
                self.exit_evt.set()
            else:
                self.error("unknown command {}".format(cmd))
        except:
            traceback.print_exc()

    def __send(self, data):
        if self.client:
            self.client.send(repr(data))

    def __shutdown(self):
        self.info("Worker [{0}] is exiting ...".format(self.device.name))
        self.__notify_client_offline()
        # A timer to make sure the notification be sent to UI.
        time.sleep(1)
        if self.client:
            self.client.shutdown()
        self.client = None
        self.running.value = 0

    def __notify_client_online(self):
        self.__send({"type" : "workerConnected",
                     "data" : { "type"         : self.dev_type,
                                "platform"     : self.platform.name,
                                "name"         : self.device.name,
                                "ip"           : self.ip,
                                "worker"       : self.uuid}})
    def __notify_client_offline(self):
        self.__send({"type" : "workerLost",
                     "data" : { "worker"       : self.uuid}})

class OpenCLGAClient(Logger):
    def __init__(self, ip, port=12345):
        Logger.__init__(self)
        self.__workerProcesses = []
        self.create_workers_for_devices(ip, port)
        self.start_workers()

    def create_workers_for_devices(self, ip, port):
        # This is a workaround for Mac Intel Drivers. We will get an error:
        # pyopencl.cffi_cl.LogicError: clGetContextInfo failed: INVALID_CONTEXT
        # if we try to use get_devices() in this process. So, we create an extra
        # process to read all platforms and devices. After that, we can create
        # device and command queue without this error.
        p_p, c_p = Pipe()
        p = Process(target=query_devices, args=(c_p,))
        p.start()
        device_list = p_p.recv()
        p.join()
        for dev in device_list:
            self.__fork_process(dev[0], dev[1], ip, port)

    def __fork_process(self, platform_index, device_index, ip, port):
        process = OpenCLGAWorker(platform_index, device_index, ip, port)
        self.__workerProcesses.append(process)

    def start_workers(self):
        for worker in self.__workerProcesses:
            worker.start()

    def stop_workers(self):
        for worker in self.__workerProcesses:
            self.info('process {} is alive ? {}'.format(worker, worker.is_alive()))
            if worker.is_alive():
                worker.terminate()
        self.__workerProcesses = []

    def shutdown(self):
        self.stop_workers()

    def is_alive(self):
        alive = True
        for worker in self.__workerProcesses:
            alive = alive and worker.is_alive()
        return alive

def start_ocl_ga_client(server="127.0.0.1", port=12345):
    global oclClient
    assert oclClient == None
    logger = Logger()
    oclClient = OpenCLGAClient(server, port)
    try:
        while True:
            if not oclClient.is_alive():
                logger.info("[OpenCLGAClient] Bye Bye !!")
                break
            time.sleep(0.01)
    except KeyboardInterrupt:
        oclClient.shutdown()
    oclClient = None

if __name__ == '__main__':
    from ocl_ga import OpenCLGA
    from utilities.generaltaskthread import Logger
    from utilities.socketserverclient import Client, OP_MSG_BEGIN, OP_MSG_END
    parser = argparse.ArgumentParser(description='oclGA client help')
    parser.add_argument('server', metavar='ip', type=str,
                        help='the server ip or address')
    args = parser.parse_args()
    start_ocl_ga_client(args.server)
