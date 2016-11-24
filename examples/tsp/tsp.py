# We need to put ancenstor directory in sys.path to let us import utils and algorithm
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# start to import what we want.
import math
import random
from itertools import tee
from time import time
from utils import create_chromosomes_by_cityids, custom_mutate, custom_crossover,\
                  calc_linear_distance, calc_spherical_distance, init_rand_seed,\
                  get_params, plot_result
from algorithm import BaseGeneticAlgorithm

class TSPGA(BaseGeneticAlgorithm):
    def __init__(self, city_info, chromosomes):
        BaseGeneticAlgorithm.__init__(self, chromosomes)
        self.city_info = city_info

    def calc_distance(self, chromosome):
        # city_ids [1,2,3,4,...N]
        city_ids = [DNAs[0] for DNAs in chromosome.dna]
        # city_ids => [1,2,3,4,...N,1]
        city_ids += [city_ids[0]]
        starts, ends = tee(city_ids)
        next(ends, None)
        # paired_city_ids => [(1,2),(2,3),(3,4),...,(N,1)]
        paired_city_ids = zip(starts, ends)

        total_dist = 0
        for s, e in paired_city_ids:
            x1, y1 = self.city_info[s]
            x2, y2 = self.city_info[e]
            dist = calc_linear_distance(x1, y1, x2, y2)
            # dist = calc_spherical_distance(x1, y1, x2, y2)
            total_dist += dist

        return total_dist

    def evaluate_fitness(self, chromosomes):
        for chromosome in chromosomes:
            fitness = -1 * self.calc_distance(chromosome)
            self.update_chromosome_fitness(chromosome, fitness)

def print_all_chromosomes(cs):
    for c in cs:
        print(c.dna)

def run(num_cities, num_chromosomes, generations):
    init_rand_seed()
    city_ids = list(range(1, num_cities + 1))
    city_info = {city_id: (random.random() * 100, random.random() * 100) for city_id in city_ids}

    chromosomes = create_chromosomes_by_cityids(num_chromosomes, city_ids)
    # print_all_chromosomes(chromosomes)

    tsp_ga = TSPGA(city_info, chromosomes)
    tsp_ga.set_customized_crossover_func(custom_crossover)
    tsp_ga.set_customized_mutate_func(custom_mutate)

    prob_mutate = 0.10
    prob_cross = 0.50
    tsp_ga.run(generations, prob_mutate, prob_cross)

    best = tsp_ga.get_best()
    best_dist = tsp_ga.calc_distance(best)
    print("best distance =", best_dist)
    print("run took", tsp_ga.elapsed_time, "seconds")
    print("best =", best.dna)

    result_ids = [g[0] for g in best.dna]
    plot_result(city_info, result_ids)
    # print("avg eval time :", tsp_ga.get_avg_evaluation_time(), "seconds.")

if __name__ == '__main__':
    cites, chromosomes, gens = get_params()
    run(num_cities=cites, num_chromosomes=chromosomes, generations=gens)
