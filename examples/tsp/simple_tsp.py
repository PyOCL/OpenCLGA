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

    tsp_path = os.path.dirname(os.path.abspath(__file__))
    ocl_kernels = os.path.realpath(os.path.join(tsp_path, "..", "..", "kernel"))
    tsp_kernels = os.path.join(tsp_path, "kernel")

    f = open(os.path.join(tsp_kernels, "simple_tsp.c"), "r")
    fstr = "".join(f.readlines())
    f.close()

    pointX = [str(city_info[v][0]) for v in city_info];
    pointY = [str(city_info[v][1]) for v in city_info]

    tsp_ga_cl = OpenCLGA(sample, generations, num_chromosomes, fstr, "simple_tsp_fitness",
                         [{"t": "float", "v": pointX, "n": "x"},
                          {"t": "float", "v": pointY, "n": "y"}],
                         [ocl_kernels], opt = "min")

    tsp_ga_cl.prepare()

    prob_mutate = 0.1
    prob_cross = 0.8
    tsp_ga_cl.run(prob_mutate, prob_cross)

    print("run took", tsp_ga_cl.elapsed_time, "seconds")
    best_chromosome, best_fitness, best_info = tsp_ga_cl.get_the_best()
    print("Best Fitness: %f"%(best_fitness))
    print("Shortest Path: " + " => ".join(str(g) for g in best_chromosome))
    utils.plot_tsp_result(city_info, best_chromosome)

if __name__ == '__main__':
    run(num_chromosomes=4000, generations=500)
