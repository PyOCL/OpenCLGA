# We need to put ancenstor directory in sys.path to let us import utils and algorithm
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# start to import what we want.
import time
import random
import pickle
import traceback
import threading
from ocl_ga import OpenCLGA
from ocl_ga_client import start_ocl_ga_client, IOpenCLGA

class TaiwanTravelThread(threading.Thread):
    def __init__(self, tsp_ga_cl):
        threading.Thread.__init__(self)
        self.__tsp_ga_cl = tsp_ga_cl

    def run(self):
        prob_mutate = 0.10
        prob_cross = 0.80
        self.__tsp_ga_cl.run(prob_mutate, prob_cross)

        if not self.__tsp_ga_cl.paused:
            best_chromosome, best_fitness, best_info = self.__tsp_ga_cl.get_the_best()
            print("Best Fitness: %f"%(best_fitness))
            print("Shortest Path: " + " => ".join(g["name"] for g in best_info.dna))

def show_generation_info(index, data_dict):
    msg = "{0}\t\t==> {1}".format(index, data_dict["best"])
    print(msg)

class TaiwanTravel(IOpenCLGA):
    def __init__(self):
        print("[Example] TaiwanTravel is created")
        self.tsp_path = None
        self.saved_filename = ""
        self.city_info = {}
        self.tsp_ga_cl = None
        self.ttthread = None

    def shutdown(self):
        if self.tsp_ga_cl:
            self.tsp_ga_cl.stop()
        if self.ttthread:
            self.ttthread.join()
        self.ttthread = None
        self.tsp_ga_cl = None
        self.tsp_path = None
        pass

    def prepare(self, dict_info):
        self.tsp_ga_cl = OpenCLGA(dict_info)
        self.tsp_path = dict_info.get("tsp_path", "")
        self.city_info = dict_info.get("city_info", {})
        self.saved_filename = dict_info.get("saved_filename", "")

        if os.path.isfile(os.path.join(self.tsp_path, self.saved_filename)):
            print("%s found, we will resume previous execution"%(self.saved_filename))
            print("resuming ...")
            self.tsp_ga_cl.restore(os.path.join(self.tsp_path, self.saved_filename))
        else:
            self.tsp_ga_cl.prepare()

        # TODO : Need to close the thread gracefully.
        if self.ttthread:
            self.ttthread.join()
            self.ttthread = None

        self.ttthread = TaiwanTravelThread(self.tsp_ga_cl)

    def run(self):
        self.ttthread.start()

    def pause(self):
        print("pausing ...")
        self.tsp_ga_cl.pause()

    def save(self):
        print("saving ...")
        assert self.saved_filename != ""
        print(self.saved_filename)
        self.tsp_ga_cl.save(os.path.join(self.tsp_path, self.saved_filename))

    def stop(self):
        print("force stop")
        self.tsp_ga_cl.stop()

    def get_statistics(self):
        print("getting statistics ...")
        st = self.tsp_ga_cl.get_statistics()
        return st

    def get_the_best(self):
        print("getting the best ...")
        best_chromosome, best_fitness, best_info = self.tsp_ga_cl.get_the_best()
        return best_chromosome

    def get_city_info(self):
        return self.city_info

if __name__ == '__main__':
    start_ocl_ga_client()
