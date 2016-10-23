import math
import random
from itertools import tee
from time import time
from utils import create_chromosomes_by_cityids, custom_mutate, custom_crossover,\
                  calc_linear_distance, calc_spherical_distance
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

def run(num_cities=20, num_chromosomes=500, generations=5000):
    random.seed(100)
    city_ids = list(range(1, num_cities + 1))
    city_info = {city_id: (random.random() * 100, random.random() * 100) for city_id in city_ids}

    rs = random.randint(1, 1)
    random.seed(rs)

    chromosomes = create_chromosomes_by_cityids(num_chromosomes, city_ids)

    tsp_ga = TSPGA(city_info, chromosomes)
    tsp_ga.set_customized_crossover_func(custom_crossover)
    tsp_ga.set_customized_mutate_func(custom_mutate)

    prob_mutate = 0.10
    prob_cross = 0.50
    best = tsp_ga.run(generations, prob_mutate, prob_cross)

    best_dist = tsp_ga.calc_distance(best)
    print("run took", tsp_ga.elapsed_time, "seconds")
    print("best =", best.dna)
    print("best distance =", best_dist)
    print("avg eval time :", tsp_ga.get_avg_evaluation_time(), "seconds.")
if __name__ == '__main__':
    run()
