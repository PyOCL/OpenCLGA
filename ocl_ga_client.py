#!/usr/bin/python3
import argparse
import pickle
import pyopencl as cl
import random
import tempfile
import threading
import time

from logger import Logger
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

    def run(self):
        random.seed()
        self.logger = Logger()
        self.notifier = threading.Condition()
        self.create_context()
        self.logger.info("Worker created for context {}".format(self.device.name))
        self.logger.info("Worker [{0}] connect to server {1}:{2}".format(
                            self.device.name, self.server, self.port))
        self.client = Client(self.server, self.port)
        self.client.setup_callbacks_info({0 : { "pre" : OP_MSG_BEGIN,
                                                "post": OP_MSG_END,
                                                "callback" : self.process_data}})
        self.send({"type": "device_info",
                   "device_name": self.device.name})
        self.logger.info("Worker [{0}] wait for commands".format(self.device.name))
        self.notifier.acquire()
        self.notifier.wait()
        self.notifier.release()

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

    def run_ocl_ga(self, prob_mutate=0.1, prob_cross=0.8):
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
        elif cmd == "save":
            state_file = tempfile.NamedTemporaryFile(delete=False)
            state_file.close()
            self.ocl_ga.save(state_file.name)
            fd = open(state_file.name, 'rb')
            self.send({"type": "save",
                       "result": fd.read()})
            fd.close()
        elif cmd == "best":
            self.send({"type": "best",
                       "result": self.ocl_ga.get_the_best()})
        elif cmd == "statistics":
            self.send({"type": "statistics",
                       "result": self.ocl_ga.get_statistics()})
        elif cmd == "run":
            self.ocl_ga_thread = threading.Thread(target=self.run_ocl_ga)
            self.ocl_ga_thread.start()
        elif cmd == "exit":
            self.client.shutdown()
            self.notifier.acquire()
            self.notifier.notifyAll()
            self.notifier.release()
            self.alive = False
        else:
            self.logger.error("unknown command {}".format(cmd))

    def send(self, data):
        self.client.send(repr(data))

class OpenCLGAClient():
    def __init__(self, server, port=12345):
        self.__workerProcesses = []
        self.create_workers_for_devices(server, port)
        self.start_workers()

    def create_workers_for_devices(self, server, ip):
        devices = []
        platforms = cl.get_platforms()
        self.__fork_process(0, 0, server, ip)
        # for pidx in range(len(platforms)):
        #     devices = platforms[pidx].get_devices()
        #     for didx in range(len(devices)):
        #         self.__fork_process(pidx, didx, server, ip)

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
