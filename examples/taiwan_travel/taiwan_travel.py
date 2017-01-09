# We need to put ancenstor directory in sys.path to let us import utils and algorithm
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# start to import what we want.
import random
import json
import signal
import threading
import utils
from pathlib import Path
from ocl_ga import OpenCLGA
from shuffler_chromosome import ShufflerChromosome
from simple_gene import SimpleGene

class TaiwanTravelThread(threading.Thread):
    def __init__(self, tsp_ga_cl, city_info):
        threading.Thread.__init__(self)
        self.__tsp_ga_cl = tsp_ga_cl
        self.__city_info = city_info

    def run(self):
        self.paused = False
        prob_mutate = 0.10
        prob_cross = 0.80
        self.__tsp_ga_cl.run(prob_mutate, prob_cross)

        if not self.paused:
            best_chromosome, best_fitness = self.__tsp_ga_cl.get_the_best()
            print("Shortest Path: " + " => ".join(str(g) for g in best_chromosome))
            utils.plot_tsp_result(self.__city_info, best_chromosome)

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
            city_id = len(cities)
            city_info[city_id - 1] = (float(city["Longitude"]), float(city["Latitude"]))
            city_infoX.append(float(city["Longitude"]))
            city_infoY.append(float(city["Latitude"]))

    return cities, city_info, city_infoX, city_infoY

def run(num_chromosomes, generations):
    cities, city_info, city_infoX, city_infoY = read_all_cities("TW319_368Addresses-no-far-islands.json")
    city_ids = list(range(len(cities)))
    random.seed()

    tsp_path = os.path.dirname(os.path.abspath(__file__))
    ocl_kernels = os.path.realpath(os.path.join(tsp_path, "..", "..", "kernel"))
    tsp_kernels = os.path.join(tsp_path, "kernel")

    sample = ShufflerChromosome([SimpleGene(v, city_ids) for v in city_ids])
    f = open(os.path.join(tsp_kernels, "taiwan_fitness.c"), "r")
    fstr = "".join(f.readlines())
    f.close()

    fstr = "#define TAIWAN_POINT_X {" + ", ".join([str(v) for v in city_infoX]) + "}\n" +\
           "#define TAIWAN_POINT_Y {" + ", ".join([str(v) for v in city_infoY]) + "}\n" +\
           fstr

    sample.use_improving_only_mutation("improving_only_mutation_helper")
    tsp_ga_cl = OpenCLGA(sample, generations, num_chromosomes, fstr, "taiwan_fitness", None,
                         [ocl_kernels], opt = "min")

    if os.path.isfile(os.path.join(tsp_path, "test.pickle")):
        print("test.pickle found, we will resume previous execution")
        tsp_ga_cl.restore(os.path.join(tsp_path, "test.pickle"))
    else:
        tsp_ga_cl.prepare()

    def signal_handler(signal, frame):
        print("You pressed Ctrl+C! We will try to pause execution before exit!")
        if ttt.is_alive():
            ttt.paused = True
            tsp_ga_cl.pause()
            ttt.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    ttt = TaiwanTravelThread(tsp_ga_cl, city_info)
    ttt.start()

    while(True):
        user_input = input("(p for pause, r for resume, s for save)")
        if "p" == user_input:
            ttt.paused = True
            tsp_ga_cl.pause()
        elif "r" == user_input:
            ttt = TaiwanTravelThread(tsp_ga_cl, city_info)
            ttt.start()
        elif "s" == user_input:
            tsp_ga_cl.save(os.path.join(tsp_path, "test.pickle"))

if __name__ == '__main__':
    run(num_chromosomes=1000, generations=11)
