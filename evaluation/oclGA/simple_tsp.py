# We need to put ancenstor directory in sys.path to let us import utils and algorithm
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# start to import what we want.
import random
import utils
from pyopencl import array as clarray
from ocl_ga import OpenCLGA
from shuffler_chromosome import ShufflerChromosome
from simple_gene import SimpleGene

def run(num_chromosomes, generations):
    num_cities = 20
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

    prob_mutate = 0.2
    prob_cross = 0.8
    tsp_ga_cl.run(prob_mutate, prob_cross)

    print("run took", tsp_ga_cl.elapsed_time, "seconds")
    best = tsp_ga_cl.best
    print("Shortest Path: " + " => ".join(str(g) for g in best))

    utils.plot_result(city_info, best)

if __name__ == '__main__':
    run(num_chromosomes=1000, generations=500)
