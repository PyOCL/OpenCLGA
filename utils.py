import random
from gene import Gene
from chromosome import Chromosome
from math import pi, sqrt, asin, cos, sin, pow

def get_params():
    return 20, 200, 5000

def init_rand_seed():
    random.seed(119)

def calc_linear_distance(x1, y1, x2, y2):
    return sqrt((x2 - x1)**2 + (y2 - y1)**2)

def calc_spherical_distance(x1, y1, x2, y2):
    def rad(deg):
        return deg * pi / 180.0
    rad_x1 = rad(x1)
    rad_x2 = rad(x2)
    a = rad_x1 - rad_x2
    b = rad(y1) - rad(y2)
    s = 2 * asin(sqrt(pow(sin(a/2),2)+cos(rad_x1)*cos(rad_x2)*pow(sin(b/2),2)))
    s = s * 6378.137
    s = round( s * 10000 ) / 10000
    return s

def create_chromosomes_by_shuffling(num_of_chromosomes, candidates, name_template="{0}"):
    chromosomes = []
    s = set(candidates)
    for x in range(num_of_chromosomes):
        genes = []
        random.shuffle(candidates)
        for item in candidates:
            g = Gene([item], elements=s, name=name_template.format(str(item)))
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

def plot_result(city_info, city_ids):
    import matplotlib.pyplot as plt
    x = []
    y = []
    for c_id in city_ids:
        x.append(city_info[c_id][0])
        y.append(city_info[c_id][1])
    x.append(x[0])
    y.append(y[0])

    plt.plot(x, y, 'ro-')
    plt.ylabel('y')
    plt.xlabel('x')
    plt.show()
