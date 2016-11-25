# We need to put ancenstor directory in sys.path to let us import utils and algorithm
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# start to import what we want.
import os
import math
import random
import pyopencl as cl
import numpy
from time import time
from itertools import tee
from pyopencl import array as clarray
from utils import create_chromosomes_by_shuffling, custom_mutate, custom_crossover,\
                calc_spherical_distance, calc_linear_distance, init_rand_seed,\
                get_params
from algorithm import BaseGeneticAlgorithm
from pprint import pprint

class TSPGACL(BaseGeneticAlgorithm):
    def __init__(self, city_info, chromosomes):
        BaseGeneticAlgorithm.__init__(self, chromosomes)
        self.city_info = city_info
        self.city_points = list(city_info.values())

        self.ctx = cl.create_some_context()
        self.queue = cl.CommandQueue(self.ctx)
        f = open('../../kernel/tsp_cl_fitness.c', 'r')
        fstr = "".join(f.readlines())
        f.close()
        self.mem_pool =cl.tools.MemoryPool(cl.tools.ImmediateAllocator(self.queue))
        self.prg = cl.Program(self.ctx, fstr).build();

        pointType = numpy.dtype([('x', numpy.float32), ('y', numpy.float32)])
        # Add a duplicated city_point[0] in front of the list of city_points.
        # Makes it easier to access for kernel.
        expanded_city_points = [self.city_points[0]] + self.city_points
        self.dev_points = clarray.to_device(self.queue,
                                            numpy.array(expanded_city_points, dtype=pointType),
                                            allocator=self.mem_pool)

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
            # dist = calc_linear_distance(x1, y1, x2, y2)
            dist = calc_spherical_distance(x1, y1, x2, y2)
            total_dist += dist

        return total_dist

    def evaluate_fitness(self, chromosomes):
        # Make a list of all chromosomes's dna in sequence, and put the 1st dna
        # element of each chromosome at the end of their own DNAs
        # e.g. The DNAs of chromosome 1 : [[1], [3], [2], [4]]
        #      The DNAs of chromosome 2 : [[4], [2], [3], [1]]
        #      chromosomesArray ==> [1,3,2,4,1, 4,2,3,1,4]
        lenght_of_chromosome = 0
        chromosomesArray = []
        for c in chromosomes:
            if lenght_of_chromosome == 0:
                lenght_of_chromosome = c.num_of_genes
            # Each chromosome's length should be the same
            assert lenght_of_chromosome == c.num_of_genes
            for g in c.dna:
                chromosomesArray += g
            chromosomesArray += c.dna[0]

        num_of_chromosomes = len(chromosomes)
        distances = numpy.zeros(num_of_chromosomes, dtype=numpy.float32)

        mf = cl.mem_flags

        dev_chromosomes = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR,
                                    hostbuf=numpy.array(chromosomesArray, dtype=numpy.int32))
        dev_distances = cl.Buffer(self.ctx, mf.WRITE_ONLY,
                                  distances.nbytes)
        cl.enqueue_copy(self.queue, dev_distances, distances)
        exec_evt = self.prg.tsp_fitness(self.queue,
                                        (num_of_chromosomes,),
                                        (1,),
                                        self.dev_points.data,
                                        dev_chromosomes,
                                        dev_distances,
                                        numpy.int32(len(self.city_points)+1),
                                        numpy.int32(num_of_chromosomes))
        exec_evt.wait()
        cl.enqueue_read_buffer(self.queue, dev_distances, distances).wait()
        # The larger distance is the weaker fitness, so make it -1*distance.
        for idx, distance in enumerate(distances):
            self.update_chromosome_fitness(chromosomes[idx], -1*distance)

def run(num_cities, num_chromosomes, generations):
    init_rand_seed()
    city_ids = list(range(1, num_cities + 1))
    city_info = {city_id: (random.random() * 100, random.random() * 100) for city_id in city_ids}

    chromosomes = create_chromosomes_by_shuffling(num_chromosomes, city_ids)

    tsp_ga_cl = TSPGACL(city_info, chromosomes)
    tsp_ga_cl.set_customized_crossover_func(custom_crossover)
    tsp_ga_cl.set_customized_mutate_func(custom_mutate)

    prob_mutate = 0.10
    prob_cross = 0.50
    tsp_ga_cl.run(generations, prob_mutate, prob_cross)
    best = tsp_ga_cl.get_best()
    print("run took", tsp_ga_cl.elapsed_time, "seconds")
    print("best =", best.dna)
    print("best distance =", tsp_ga_cl.calc_distance(best))
    print("avg eval time :", tsp_ga_cl.get_avg_evaluation_time(), "seconds.")
if __name__ == '__main__':
    cites, chromosomes, gens = get_params()
    run(num_cities=cites, num_chromosomes=chromosomes, generations=gens)
