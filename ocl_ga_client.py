#!/usr/bin/python3
import pyopencl as cl
import time
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
        self.__server_ip = ip
        self.__server_port = port
        self.__workerProcesses = []
        self.__list_devices()
        self.__start()
        time.sleep(5)
        self.__stop()
        #TODO: try to fork as more as possible process to host each context and connect to server.

    def __connect():
        pass

    def __send(self, command, data):
        pass

    def __process_data(self, data):
        pass

    def __list_devices(self):
        devices = []
        platforms = cl.get_platforms()
        for pidx in range(len(platforms)):
            devices = platforms[pidx].get_devices()
            for didx in range(len(devices)):
                self.__fork_process(pidx, didx)

    def __fork_process(self, platform_index, device_index):
        self.__workerProcesses.append(OpenCLGAWorker(platform_index, device_index))

    def __start(self):
        for worker in self.__workerProcesses:
            worker.start()

    def __stop(self):
        for worker in self.__workerProcesses:
            print('process is alive'.format(worker.is_alive()))
            worker.terminate()

if __name__ == '__main__':
    OpenCLGAClient("0.0.0.0")
