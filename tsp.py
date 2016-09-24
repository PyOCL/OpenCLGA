import math
import random
from itertools import tee
from time import time
from algorithm import BaseGeneticAlgorithm

def custom_mutate(c1, prob):
    ori_candidates = range(c1.num_of_genes)
    for idx1 in ori_candidates:
        if random.random() < prob:
            candidates_remain = [x for x in ori_candidates if x != idx1]
            idx2 = random.sample(candidates_remain, 1)[0]
            c1.swap(idx1, idx2)

def custom_crossover(c1, c2, point):
    for i in range(c1.num_of_genes):
        if c1.dna[i] == c2.dna[point]:
            c1.swap(point, i)
            break

class TSPGA(BaseGeneticAlgorithm):
    def __init__(self, city_info, chromosomes):
        BaseGeneticAlgorithm.__init__(self, chromosomes)
        self.city_info = city_info

    def calc_distance(self, chromosome):
        city_ids = [DNAs[0] for DNAs in chromosome.dna]
        city_ids += [city_ids[0]]
        starts, ends = tee(city_ids)
        next(ends, None)
        paired_city_ids = zip(starts, ends)

        total_dist = 0
        for s, e in paired_city_ids:
            x1, y1 = self.city_info[s]
            x2, y2 = self.city_info[e]
            dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            total_dist += dist

        return total_dist

    def evaluate_fitness(self, chromosomes):
        for chromosome in chromosomes:
            fitness = -1 * self.calc_distance(chromosome)
            self.update_chromosome_fitness(chromosome, fitness)

def create_chromosomes_by_cityids(num_of_chromosomes, city_ids):
    from gene import Gene
    from chromosome import Chromosome

    chromosomes = []
    for x in range(num_of_chromosomes):
        genes = []

        for city_id in city_ids:
            g = Gene([city_id], elements=set(city_ids), name='city %s'%str(x))
            genes.append(g)

        c = Chromosome(genes)
        chromosomes.append(c)

    return chromosomes

def run(num_cities=20, num_chromosomes=100, generations=2500):
    random.seed(100)
    city_ids = list(range(1, num_cities + 1))
    city_info = {city_id: (random.random() * 100, random.random() * 100) for city_id in city_ids}

    rs = random.randint(1, int(time()))
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

if __name__ == '__main__':
    run()
