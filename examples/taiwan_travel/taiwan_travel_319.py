# We need to put ancenstor directory in sys.path to let us import utils and algorithm
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# start to import what we want.
import json
import math
import random
import utils
from itertools import tee
from pathlib import Path
from time import time
from algorithm import BaseGeneticAlgorithm

class TSPGA(BaseGeneticAlgorithm):
    def __init__(self, cities, city_info, chromosomes):
        BaseGeneticAlgorithm.__init__(self, chromosomes)
        self.cities = cities
        self.city_info = city_info

    def calc_distance(self, chromosome):
        # city_ids [1,2,3,4,...N]
        city_ids = [dnas[0] for dnas in chromosome.dna]
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
            dist = utils.calc_spherical_distance(x1, y1, x2, y2)
            total_dist += dist

        return total_dist

    def evaluate_fitness(self, chromosomes):
        for chromosome in chromosomes:
            fitness = -1 * self.calc_distance(chromosome)
            self.update_chromosome_fitness(chromosome, fitness)

def read_all_cities(file_name):
    cities_text = Path(file_name).read_text(encoding="UTF-8")
    cities_groups = json.loads(cities_text);
    cities = []
    city_info = {}
    for group in cities_groups.keys():
        for city_key in cities_groups[group]:
            city = cities_groups[group][city_key]
            cities.append({"x": float(city["Longitude"]), "y": float(city["Latitude"]),
                           "address": city["Address"], "name": city["Name"]})
            city_id = len(cities)
            city_info[city_id] = (float(city["Longitude"]), float(city["Latitude"]))

    return cities, city_info

def run(num_chromosomes, generations):
    cities, city_info = read_all_cities("TW319_368Addresses-no-far-islands.json")
    city_ids = list(range(1, len(cities) + 1))
    random.seed()

    chromosomes = utils.create_chromosomes_by_shuffling(num_chromosomes, city_ids)

    tsp_ga = TSPGA(cities, city_info, chromosomes)
    tsp_ga.set_customized_crossover_func(utils.custom_crossover)
    tsp_ga.set_customized_mutate_func(utils.custom_mutate)

    prob_mutate = 0.10
    prob_cross = 0.50
    tsp_ga.run(generations, prob_mutate, prob_cross)

    best = tsp_ga.get_best()
    best_dist = tsp_ga.calc_distance(best)
    print("best distance =", best_dist)
    print("run took", tsp_ga.elapsed_time, "seconds")
    print("best =", [g.name for g in best.genes])

    result_ids = [g[0] for g in best.dna]
    utils.plot_result(city_info, result_ids)
    print("avg eval time :", tsp_ga.get_avg_evaluation_time(), "seconds.")

if __name__ == '__main__':
    run(num_chromosomes=10, generations=50)
