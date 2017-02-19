#!/usr/bin/python3

from ocl_ga import OpenCLGA

class OpenCLGAClient(OpenCLGA):

    def __init__(self, ip, port=12345):
        self.__server_ip = ip
        self.__server_port = port

    def __connect():
        pass

    def __send(self, command, data):
        pass

    def __process_data(self, data):
        pass

    # public APIs
    def prepare(self):
        raise RuntimeError("OpenCL Client doesn't support this one")

    def run(self, prob_mutate, prob_crossover):
        raise RuntimeError("OpenCL Client doesn't support this one")

    def pause(self):
        raise RuntimeError("OpenCL Client doesn't support this one")

    def save(self, filename):
        raise RuntimeError("OpenCL Client doesn't support this one")

    def restore(self, filename):
        raise RuntimeError("OpenCL Client doesn't support this one")

    def get_statistics(self):
        raise RuntimeError("OpenCL Client doesn't support this one")

    def get_the_best(self):
        raise RuntimeError("OpenCL Client doesn't support this one")
