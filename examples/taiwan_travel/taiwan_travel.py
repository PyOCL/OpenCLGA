# We need to put ancenstor directory in sys.path to let us import utils and algorithm
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# start to import what we want.
import random
import json
import utils
from pathlib import Path
from ocl_ga import OpenCLGA
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

    tsp_ga_cl = OpenCLGA(sample, generations, num_chromosomes, fstr, "taiwan_fitness", None,
                         [ocl_kernels])

    prob_mutate = 0.10
    prob_cross = 0.80
    tsp_ga_cl.run(prob_mutate, prob_cross)

    print("run took", tsp_ga_cl.elapsed_time, "seconds")
    best = tsp_ga_cl.best
    print("Shortest Path: " + " => ".join(cities[g]["name"] for g in best))

    utils.plot_result(city_info, best)

if __name__ == '__main__':
    run(num_chromosomes=1000, generations=200)
