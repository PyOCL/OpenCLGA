#!/usr/bin/python3
import pyopencl as cl
import socket
import time
import threading
from multiprocessing import Process
from ocl_ga import OpenCLGA
# note: we can use multiprocessing.Queue or multiprocessing.Value to exchange data
class OpenCLGAWorker(Process):
    def __init__(self, platform_index, device_index):
        super().__init__()
        self.__platform_index = platform_index
        self.__device_index = device_index

    def __create_context(self):
        platform = cl.get_platforms()[self.__platform_index]
        self.__device = platform.get_devices()[self.__device_index]
        self.__context = cl.Context(devices=[self.__device])
        return self.__context

    def run(self):
        self.__create_context()
        print('Worker started for context {}'.format(self.__device.name))


class OpenCLGAClient():
    def __init__(self, ip, port=12345):
        self.alive = True
        self.__server_ip = ip
        self.__server_port = port
        self.__workerProcesses = []
        self.__create_workers_for_devices()
        self.__start_workers()
        #TODO: try to fork as more as possible process to host each context and connect to server.
        self.client = None
        self.__connect()

    def __connect(self):
        from server_client import Client, OP_MSG_BEGIN, OP_MSG_END
        self.client = Client(self.__server_ip, self.__server_port)
        self.client.setup_callbacks_info({0 : { "pre" : OP_MSG_BEGIN,
                                                "post": OP_MSG_END,
                                                "callback" : self.__process_data}})
        pass

    def __send(self, command, data):
        if self.client:
            self.client.send(data)
        pass

    def __process_data(self, data):
        print("[Client] processing data : %s"%(str(data)))
        if data == bytearray("exit", "ASCII"):
            self.__shutdown()
        else:
            self.__send("cmd", str(data) + "_back")
        pass

    def __create_workers_for_devices(self):
        devices = []
        platforms = cl.get_platforms()
        for pidx in range(len(platforms)):
            devices = platforms[pidx].get_devices()
            for didx in range(len(devices)):
                self.__fork_process(pidx, didx)

    def __fork_process(self, platform_index, device_index):
        self.__workerProcesses.append(OpenCLGAWorker(platform_index, device_index))

    def __start_workers(self):
        for worker in self.__workerProcesses:
            worker.start()

    def __stop_workers(self):
        for worker in self.__workerProcesses:
            print('process is alive'.format(worker.is_alive()))
            worker.terminate()
        self.__workerProcesses = []

    def __shutdown(self):
        if self.client:
            self.client.shutdown()
        self.client = None
        self.__stop_workers()
        self.alive = False

    def shutdown(self):
        self.__shutdown()

    def is_alive(self):
        return self.alive

if __name__ == '__main__':
    oclClient = OpenCLGAClient("127.0.0.1")
    try:
        while True:
            if not oclClient.is_alive():
                print("[OpenCLGAClient] Bye Bye !!")
                break
            time.sleep(0.01)
    except KeyboardInterrupt:
        oclClient.shutdown()
    oclClient = None
