import os
import sys
# We need to put ancenstor directory in sys.path to let us import utils and algorithm
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import time
import json
import utils
import random
import pickle
import traceback
from pathlib import Path
from shuffler_chromosome import ShufflerChromosome
from simple_gene import SimpleGene

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
                 "saved_filename" : "test%d%d.pickle",
                 "prob_mutation" : 0.1,
                 "prob_crossover" : 0.8,}
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

def show_generation_info(index, data_dict):
    msg = "{0}\t\t==> {1}".format(index, data_dict["best"])
    print(msg)

def run_ocl_ga(ga, prob_mutation, prob_crossover):
    ga.run(prob_mutation, prob_crossover)
    print("[Local] OpenCLGA run end !")

def start_ocl_ga_local(info_getter):
    serialized_info = info_getter()
    info = pickle.loads(serialized_info)
    info['saved_filename'] = info['saved_filename']%(0, 0)
    info["generation_callback"] = show_generation_info
    prob_mutation = info['prob_mutation']
    prob_crossover = info['prob_crossover']

    import threading
    from ocl_ga import OpenCLGA
    ga_target = OpenCLGA(info)
    ga_target.prepare()
    try:
        print("Press run     + <Enter> to run")
        print("Press pause   + <Enter> to pause")
        print("Press restore + <Enter> to restore")
        print("Press save    + <Enter> to save")
        print("Press stop    + <Enter> to stop")
        print("Press plot_st    + <Enter> to plot statistics information")
        print("Press plot_best  + <Enter> to plot best information")
        print("Press ctrl    + c       to exit")
        while True:
            user_input = get_input()
            if user_input == "pause":
                ga_target.pause()
            elif user_input == "run":
                ocl_ga_thread = threading.Thread(target=run_ocl_ga, args=(ga_target, prob_mutation, prob_crossover))
                ocl_ga_thread.start()
            elif user_input == "stop":
                ga_target.stop()
            elif user_input == "plot_st":
                st = ga_target.get_statistics()
                utils.plot_ga_result(st)
            elif user_input == "plot_best":
                best_chromosome = ga_target.get_the_best()
                utils.plot_tsp_result(ga_target.get_city_info(), best_chromosome)
            elif user_input == "exit":
                break
            elif user_input == "save":
                ga_target.save()
            elif user_input == "restore":
                ga_target.restore()
    except KeyboardInterrupt:
        traceback.print_exc()

if __name__ == '__main__':
    print("Press 1 + <Enter> to run as a OCL GA Server for remote clients.")
    print("Press 2 + <Enter> to run Taiwan Travel OCL GA independently.")

    def callback_from_client(info):
        # TODO : Need to plot information in Mainthread.
        if "best" in info:
            cities, city_info, city_infoX, city_infoY = read_all_cities("TW319_368Addresses-no-far-islands.json")
            utils.plot_tsp_result(city_info, info["best"])
        if "statistics" in info:
            utils.plot_ga_result(info["statistics"])

    while True:
        user_input = get_input()
        if user_input == "1":
            from ocl_ga_server import start_ocl_ga_server
            start_ocl_ga_server(get_taiwan_travel_info, {"message" : callback_from_client})
            break
        elif user_input == "2":
            start_ocl_ga_local(get_taiwan_travel_info)
            break
