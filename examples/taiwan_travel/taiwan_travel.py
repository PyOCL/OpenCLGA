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
    def __init__(self, tsp_ga_cl, city_info, evt):
        threading.Thread.__init__(self)
        self.__tsp_ga_cl = tsp_ga_cl
        self.__city_info = city_info
        self.end_thread_evt = evt

    def run(self):
        prob_mutate = 0.10
        prob_cross = 0.80
        self.__tsp_ga_cl.run(prob_mutate, prob_cross)

        if not self.__tsp_ga_cl.paused:
            best_chromosome, best_fitness, best_info = self.__tsp_ga_cl.get_the_best()
            print("Best Fitness: %f"%(best_fitness))
            print("Shortest Path: " + " => ".join(g["name"] for g in best_info.dna))
            # Set the event when the task is done rather than paused.
            self.end_thread_evt.set()

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

def create_result_bitstream(tsp_ga_cl):
    best_chromosome, best_fitness, best_info = tsp_ga_cl.get_the_best()
    statistics = tsp_ga_cl.get_statistics()
    res = {"best_info" : best_info,
           "statistics" : statistics}

    result = "result.zip"
    result_bitstream = b""
    try:
        with zipfile.ZipFile(result, 'w') as myzip:
            myzip.writestr("result.info", pickle.dumps(res))

        if not os.path.exists(result):
            print("No result is created !! Empty bitstream is returned !!")
        else:
            with open(result, "rb") as fn:
                result_bitstream = fn.read()
            os.remove(result)
    except:
        traceback.print_exc()

    return result_bitstream


def get_input():
    input_data = None
    if sys.platform in ["linux", "darwin"]:
        import select
        if select.select([sys.stdin], [], [], 0.1) == ([sys.stdin], [], []):
            input_data = sys.stdin.readline().rstrip()
    elif sys.platform == "win32":
        import msvcrt
        time.sleep(0.1)
        if msvcrt.kbhit():
            input_data = msvcrt.getch().decode("utf-8")
    else:
        pass
    return input_data

def show_generation_info(index, data_dict):
    print("{0}\t\t==> {1} ~ {2}".format(index, data_dict["best"], data_dict["worst"]))

def run(num_chromosomes, generations, ext_proc):
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

    fstr = "#define TAIWAN_POINT_X {" + ", ".join([str(v) for v in city_infoX]) + "}\n" +\
           "#define TAIWAN_POINT_Y {" + ", ".join([str(v) for v in city_infoY]) + "}\n" +\
           fstr

    sample.use_improving_only_mutation("improving_only_mutation_helper")
    tsp_ga_cl = OpenCLGA({"sample_chromosome": sample,
                          "termination": {
                            "type": "time",
                            "time": 60 * 10 # 2 minutes
                          },
                          "population": num_chromosomes,
                          "fitness_kernel_str": fstr,
                          "fitness_func": "taiwan_fitness",
                          "extra_include_path": [ocl_kernels],
                          "opt_for_max": "min",
                          "generation_callback": show_generation_info})

    if os.path.isfile(os.path.join(tsp_path, "test.pickle")):
        print("test.pickle found, we will resume previous execution")
        tsp_ga_cl.restore(os.path.join(tsp_path, "test.pickle"))
    else:
        tsp_ga_cl.prepare()

    evt = threading.Event()
    evt.clear()

    def signal_handler(signal, frame):
        print("You pressed Ctrl+C! We will try to pause execution before exit!")
        if ttt.is_alive():
            tsp_ga_cl.pause()
            ttt.join()
        evt.set()

    signal.signal(signal.SIGINT, signal_handler)

    ttt = TaiwanTravelThread(tsp_ga_cl, city_info, evt)
    ttt.start()

    if ext_proc:
        # TODO : Need to find a way for input p/r/s
        while(True):
            if evt.is_set():
                signal_handler(signal.SIGINT, None)
                return create_result_bitstream(tsp_ga_cl)
            time.sleep(1)
    else:
        while 1:
            if evt.is_set():
                # The thread has done its job.
                best_chromosome, best_fitness, best_info = tsp_ga_cl.get_the_best()
                utils.plot_ga_result(tsp_ga_cl.get_statistics())
                utils.plot_tsp_result(city_info, best_chromosome)
                break
            user_input = get_input()
            if not user_input:
                # Nothing input
                pass
            else:
                if "p" == user_input:
                    print("pausing ...")
                    tsp_ga_cl.pause()
                elif "r" == user_input:
                    print("resuming ...")
                    evt.clear()
                    ttt = TaiwanTravelThread(tsp_ga_cl, city_info, evt)
                    ttt.start()
                elif "s" == user_input:
                    print("saving ...")
                    tsp_ga_cl.save(os.path.join(tsp_path, "test.pickle"))
                elif "x" == user_input:
                    print("force stop")
                    tsp_ga_cl.stop()
                else:
                    pass
    return b""

# Exposed function
def run_task(external_process = False):
    return run(num_chromosomes=4, generations=50, ext_proc=external_process)

if __name__ == '__main__':
    run_task()
