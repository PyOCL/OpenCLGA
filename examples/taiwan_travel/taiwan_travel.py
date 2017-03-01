# We need to put ancenstor directory in sys.path to let us import utils and algorithm
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# start to import what we want.
import time
import random
import pickle
import json
import signal
import zipfile
import traceback
import threading
import utils
from pathlib import Path
from ocl_ga import OpenCLGA
from shuffler_chromosome import ShufflerChromosome
from simple_gene import SimpleGene

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

def read_all_cities(file_name):
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    cities_text = Path(file_path).read_text(encoding="UTF-8")
    cities_groups = json.loads(cities_text);
    cities = []
    city_info = {}
    city_infoX = []
    city_infoY = []
    for group in cities_groups.keys():
        for city_key in cities_groups[group]:
            city = cities_groups[group][city_key]
            cities.append({"x": float(city["Longitude"]), "y": float(city["Latitude"]),
                           "address": city["Address"], "name": city["Name"]})

    # to sort cities is very important for save and restore becase the sequence of name in json
    # object is not the same.
    cities = sorted(cities, key=lambda city: -city["y"])

    for idx in range(len(cities)):
        city = cities[idx]
        city_id = idx
        city_info[city_id] = (float(city["x"]), float(city["y"]))
        city_infoX.append(float(city["x"]))
        city_infoY.append(float(city["y"]))

    return cities, city_info, city_infoX, city_infoY

def show_generation_info(index, data_dict):
    print("{0}\t\t==> {1}".format(index, data_dict["best"]))

class TaiwanTravel(object):
    def __init__(self):
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

    def plot_results(self):
        # NOTE : A workaround to ensure np_chromosome data is read from device.
        #        As we're trying to plot result right after calling break, we may
        #        get all 0 in the chromosome buffer.
        time.sleep(2)

        best_chromosome, best_fitness, best_info = self.tsp_ga_cl.get_the_best()
        utils.plot_ga_result(self.tsp_ga_cl.get_statistics())
        utils.plot_tsp_result(self.city_info, best_chromosome)

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

    def start(self):
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
        self.plot_results()

tt = None
def recv_taiwan_travel_cmddata(cmd, data, cl_ctx = None,
                               platform_index = 0, device_index = 0):
    print("[TT] cmd = %s"%(cmd))
    global tt
    if cmd == "prepare":
        if not tt:
            tt = TaiwanTravel()
        info = pickle.loads(data)
        info['cl_context'] = cl_ctx
        info['saved_filename'] = info['saved_filename']%(platform_index, device_index)
        tt.prepare(info)
    elif cmd == "run":
        assert tt != None
        tt.start()
    elif cmd == "pause":
        assert tt != None
        tt.pause()
    elif cmd == "restore":
        assert False
    elif cmd == "save":
        assert tt != None
        tt.save()
    elif cmd == "stop":
        assert tt != None
        tt.stop()
    else:
        pass

def send_taiwan_travel_cmddata(cmd, data):
    '''
    Send results or anything back to Server.
    '''
    pass

def get_taiwan_travel_info():
    '''
    NOTE : Config TaiwanTravel GA parameters in dictionary 'dict_info'.
    '''
    cities, city_info, city_infoX, city_infoY = read_all_cities("TW319_368Addresses-no-far-islands.json")
    city_ids = list(range(len(cities)))
    random.seed()

    tsp_path = os.path.dirname(os.path.abspath(__file__))
    ocl_kernels = os.path.realpath(os.path.join(tsp_path, "..", "..", "kernel"))
    tsp_kernels = os.path.join(tsp_path, "kernel")

    sample = ShufflerChromosome([SimpleGene(v, cities) for v in city_ids])
    f = open(os.path.join(tsp_kernels, "taiwan_fitness.c"), "r")
    fstr = "".join(f.readlines())
    f.close()

    # It seems we don't need to use this helper if we enlarge the population size. Please
    # re-evaluate and remove or uncomment the following line:
    # sample.use_improving_only_mutation("improving_only_mutation_helper")
    sample.repopulate_diff = {"type": "best_avg",
                              "diff": 1000}

    dict_info = {"sample_chromosome": sample,
                 "termination": { "type": "count",
                                  "count": 1000000 },
                 "population": 10240,
                 "fitness_kernel_str": fstr,
                 "fitness_func": "taiwan_fitness",
                 "fitness_args": [{"t": "float", "v": city_infoX, "n": "x"},
                                  {"t": "float", "v": city_infoY, "n": "y"}],
                 "extra_include_path": [ocl_kernels],
                 "opt_for_max": "min",
                 "generation_callback": show_generation_info,
                 "tsp_path" : tsp_path,
                 "city_info" : city_info,
                 "saved_filename" : "test%d%d.pickle"}
    serialized_info = pickle.dumps(dict_info)
    return serialized_info


lines_input = ""
def get_input():
    data = None
    try:
        if sys.platform in ["linux", "darwin"]:
            import select
            time.sleep(0.01)
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                data = sys.stdin.readline().rstrip()
        elif sys.platform == "win32":
            global lines_input
            import msvcrt
            time.sleep(0.01)
            if msvcrt.kbhit():
                data = msvcrt.getch().decode("utf-8")
                if data == "\r":
                    # Enter is pressed
                    data = lines_input
                    lines_input = ""
                else:
                    lines_input += data
                    print(data)
                    data = None
        else:
            pass
    except KeyboardInterrupt:
        data = "exit"
    return data

def start_tt_ocl_ga(standalone = False):
    if not standalone:
        from ocl_ga_client import start_ocl_ga_client
        start_ocl_ga_client(recv_taiwan_travel_cmddata, send_taiwan_travel_cmddata)
        return

    serialized_info = get_taiwan_travel_info()
    recv_taiwan_travel_cmddata("prepare", serialized_info)
    recv_taiwan_travel_cmddata("run", None)
    try:
        print("Press pause   + <Enter> to pause")
        print("Press restore + <Enter> to restore")
        print("Press save    + <Enter> to save")
        print("Press stop    + <Enter> to stop")
        print("Press ctrl    + c       to exit")
        while True:
            user_input = get_input()
            if "pause" == user_input:
                recv_taiwan_travel_cmddata("pause", None)
            elif user_input in ["stop", "exit"]:
                recv_taiwan_travel_cmddata("stop", None)
                break
            elif "save" == user_input:
                recv_taiwan_travel_cmddata("save", None)
            elif "restore" == user_input:
                recv_taiwan_travel_cmddata("prepare", serialized_info)
                recv_taiwan_travel_cmddata("run", None)
    except KeyboardInterrupt:
        traceback.print_exc()

if __name__ == '__main__':
    print("Press 1 + <Enter> to run as OCL GA Server.")
    print("Press 2 + <Enter> to run as OCL GA Client.")
    print("Press 3 + <Enter> to run Taiwan Travel OCL GA in standalone mode.")
    while True:
        user_input = get_input()
        if user_input == "1":
            from ocl_ga_server import start_ocl_ga_server
            start_ocl_ga_server(get_taiwan_travel_info)
            break
        elif user_input == "2":
            start_tt_ocl_ga(standalone = False)
            break
        elif user_input == "3":
            start_tt_ocl_ga(standalone = True)
            break
