#!/usr/bin/python3
import argparse
import pickle
import pyopencl as cl
import random
import tempfile
import threading
import time

from utilities.generaltaskthread.logger import Logger
from multiprocessing import Process
from ocl_ga import OpenCLGA
from server_client import Client, OP_MSG_BEGIN, OP_MSG_END

oclClient = None

class OpenCLGAWorker(Process):
    def __init__(self, platform_index, device_index, server, port):
        super().__init__()
        self.alive = True
        self.platform_index = platform_index
        self.device_index = device_index
        self.server = server
        self.port = port
        self.client = None
        self.notifier = None

    def terminate(self):
        if self.client:
            self.client.shutdown()
        if self.notifier:
            self.notifier.notifyAll()
        self.client = None
        self.alive = False
        self.notifier = None
        super(OpenCLGAWorker, self).terminate()

    def run(self):
        random.seed()
        self.logger = Logger()
        try:
            self.create_context()
            self.logger.info("Worker created for context {}".format(self.device.name))
            self.logger.info("Worker [{0}] connect to server {1}:{2}".format(
                                self.device.name, self.server, self.port))
        except:
            self.logger.error("Create OpenCL context failed !")
            return
        try:
            self.client = Client(self.server, self.port)
            self.client.setup_callbacks_info({0 : { "pre" : OP_MSG_BEGIN,
                                                    "post": OP_MSG_END,
                                                    "callback" : self.process_data}})
            self.send({"type": "device_info",
                       "device_name": self.device.name})
        except ConnectionRefusedError:
            self.logger.error("Connection refused! Please check Server status.")
            self.client = None
            return

        self.logger.info("Worker [{0}] wait for commands".format(self.device.name))
        self.notifier = threading.Condition()
        with self.notifier:
        # self.notifier.acquire()
            self.notifier.wait()
        # self.notifier.release()

    def create_context(self):
        platform = cl.get_platforms()[self.platform_index]
        self.device = platform.get_devices()[self.device_index]
        self.context = cl.Context(devices=[self.device])
        return self.context

    def send_and_dump_info(self, index, data):
        self.logger.verbose("{0}\t\t==> {1} ~ {2} ~ {3}".format(index, data["best"], data["avg"],
                                                                data["worst"]))
        self.send({"type": "generation_result",
                   "index": index,
                   "result": data})

    def run_ocl_ga(self, probs):
        prob_mutate, prob_cross = probs
        self.logger.info("Worker [{}]: oclGA run with {}/{}".format(self.device.name,
                                                                    prob_mutate, prob_cross))
        self.ocl_ga.run(prob_mutate, prob_cross)
        self.send({"type": "end"})

    def create_ocl_ga(self, options):
        print(options["sample_chromosome"])
        options["cl_context"] = self.context
        options["generation_callback"] = self.send_and_dump_info
        self.ocl_ga = OpenCLGA(options)
        self.ocl_ga.prepare()
        self.logger.info("Worker [{}]: oclGA prepared".format(self.device.name))

    def process_data(self, data):
        '''
        Called when data is received from server.
        '''
        global logger
        # Conver bytearray "data" to string-like object
        msg = str(data, 'ASCII')
        dict_msg = eval(msg)
        cmd = dict_msg["command"]
        payload = dict_msg["data"]
        self.logger.verbose("Worker [{}]: cmd received = {}".format(self.device.name, cmd))
        if cmd == "prepare":
            self.create_ocl_ga(pickle.loads(payload))
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
            self.send({"type": "save",
                       "result": None})
            # state_file.close()
        elif cmd == "best":
            # TODO : A workaround to get best chromesome back for TSP
            #       May need to pickle this tuple as it contains specific data structure.
            best_chromosome, best_fitness, chromesome_kernel = self.ocl_ga.get_the_best()
            self.send({"type": "best",
                       "result": repr(best_chromosome)})
        elif cmd == "statistics":
            self.send({"type": "statistics",
                       "result": self.ocl_ga.get_statistics()})
        elif cmd == "run":
            self.ocl_ga_thread = threading.Thread(target=self.run_ocl_ga, args=(payload,))
            self.ocl_ga_thread.start()
        elif cmd == "exit":
            self.client.shutdown()
            with self.notifier:
                self.notifier.notifyAll()
            self.alive = False
        else:
            self.logger.error("unknown command {}".format(cmd))

    def send(self, data):
        if self.client:
            self.client.send(repr(data))

class OpenCLGAClient():
    def __init__(self, server, port=12345):
        self.__workerProcesses = []
        self.create_workers_for_devices(server, port)
        self.start_workers()

    def create_workers_for_devices(self, server, ip):
        platforms = cl.get_platforms()
        for pidx in range(len(platforms)):
            devices = platforms[pidx].get_devices()
            for didx in range(len(devices)):
                self.__fork_process(pidx, didx, server, ip)

    def __fork_process(self, platform_index, device_index, server, ip):
        process = OpenCLGAWorker(platform_index, device_index, server, ip)
        self.__workerProcesses.append(process)

    def start_workers(self):
        for worker in self.__workerProcesses:
            worker.start()

    def stop_workers(self):
        for worker in self.__workerProcesses:
            print('process is alive'.format(worker.is_alive()))
            worker.terminate()
        self.__workerProcesses = []

    def shutdown(self):
        self.stop_workers()
        self.alive = False

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
    parser = argparse.ArgumentParser(description='oclGA client help')
    parser.add_argument('server', metavar='ip', type=str,
                        help='the server ip or address')
    args = parser.parse_args()
    start_ocl_ga_client(args.server)
