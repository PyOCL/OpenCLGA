#!/usr/bin/python3
import pyopencl as cl
from ocl_ga import OpenCLGA

class OpenCLGAClient():
    def __init__(self, ip, port=12345):
        self.__server_ip = ip
        self.__server_port = port
        self.__contexts = self.__create_cl(self.__list_devices()))
        #TODO: try to fork as more as possible process to host each context and connect to server.

    def __connect():
        pass

    def __send(self, command, data):
        pass

    def __process_data(self, data):
        pass

    def __list_devices(self):
        devices = []
        for platform in cl.get_platforms():
            for device in platform.get_devices():
                devices.append(device)
        return devices

    def __create_cl(self, devices):
        # we create one context based on device
        return [cl.Context(devices=[device]) for device in devices]

if __name__ == '__main__':
    OpenCLGAClient("0.0.0.0")
