# We need to put ancenstor directory in sys.path to let us import utils and algorithm
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# start to import what we want.
import math
import random
import pyopencl as cl
import numpy
import sys
import json
import utils
from time import time
from time import clock
from pathlib import Path
from itertools import tee
from pyopencl import array as clarray
from ocl_ga import OpenCLGA
from shuffler_chromosome import ShufflerChromosome
from simple_gene import SimpleGene
from pprint import pprint

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
    num_cities = 10
    random.seed(119)
    city_ids = list(range(0, num_cities))
    city_info = {city_id: (random.random() * 100, random.random() * 100) for city_id in city_ids}

    sample = ShufflerChromosome([SimpleGene(v, city_ids) for v in city_ids])

    f = open(os.path.join("cl", "simple_tsp.c"), "r")
    fstr = "".join(f.readlines())
    f.close()

    fstr = "#define TSP_POINT_X {" + ", ".join([str(city_info[v][0]) for v in city_info]) + "}\n" +\
           "#define TSP_POINT_Y {" + ", ".join([str(city_info[v][1]) for v in city_info]) + "}\n" +\
           fstr

    tsp_ga_cl = OpenCLGA(sample, generations, num_chromosomes, fstr, "simple_tsp_fitness",\
                         ["../../kernel"])

    prob_mutate = 0.10
    prob_cross = 0.60
    tsp_ga_cl.run(prob_mutate, prob_cross)

    print("run took", tsp_ga_cl.elapsed_time, "seconds")
    best = tsp_ga_cl.best
    print("Shortest Path: " + " => ".join(str(g) for g in best))

    utils.plot_result(city_info, best)

if __name__ == '__main__':
    run(num_chromosomes=100, generations=1000)
