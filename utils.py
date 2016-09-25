import random
from gene import Gene
from chromosome import Chromosome

def create_chromosomes_by_cityids(num_of_chromosomes, city_ids):
    chromosomes = []

    for x in range(num_of_chromosomes):
        genes = []
        random.seed(x)
        random.shuffle(city_ids)
        for city_id in city_ids:
            g = Gene([city_id], elements=set(city_ids), name='city %s'%str(x))
            genes.append(g)

        c = Chromosome(genes)
        chromosomes.append(c)

    return chromosomes

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
