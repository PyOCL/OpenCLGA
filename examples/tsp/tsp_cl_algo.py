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
import sys
from time import time
from time import clock
from itertools import tee
from pyopencl import array as clarray
from utils import create_chromosomes_by_shuffling,\
                calc_spherical_distance, calc_linear_distance, init_testing_rand_seed,\
                get_testing_params, plot_result
from algorithm import BaseGeneticAlgorithm
from pprint import pprint

class TSPGACL(BaseGeneticAlgorithm):
    def __init__(self, city_info, chromosomes):
        BaseGeneticAlgorithm.__init__(self, chromosomes)
        self.city_info = city_info
        self.city_points = list(city_info.values())

        self.ctx = cl.create_some_context()
        self.queue = cl.CommandQueue(self.ctx)

        # Define kernel_folder from where the program being exectued.
        kernel_folder = '../../kernel' if os.getcwd() == os.path.dirname(os.path.abspath(__file__)) else 'kernel'
        lstPaths = [kernel_folder]

        f = open(os.path.join(kernel_folder, 'ga_algo.c'), 'r')
        fstr = "".join(f.readlines())
        f.close()
        self.mem_pool =cl.tools.MemoryPool(cl.tools.ImmediateAllocator(self.queue))

        modifiedlstPath = []
        for path in lstPaths:
            escapedPath = path.replace(' ', '^ ') if sys.platform.startswith('win') else path.replace(' ', '\\ ')
            # After looking into the source code of pyopencl/__init__.py
            # "-I" and folder path should be sepearetd. And " should not included in string path.
            modifiedlstPath.append('-I')
            modifiedlstPath.append(os.path.join(os.getcwd(), escapedPath))
        self.prg = cl.Program(self.ctx, fstr).build(modifiedlstPath);

        pointType = numpy.dtype([('x', numpy.float32), ('y', numpy.float32)])
        # Add a duplicated city_point[0] in front of the list of city_points.
        # Makes it easier to access for kernel.
        expanded_city_points = [self.city_points[0]] + self.city_points
        self.dev_points = clarray.to_device(self.queue,
                                            numpy.array(expanded_city_points, dtype=pointType),
                                            allocator=self.mem_pool)

        self.set_customized_run_impl(self.run_impl)

    def evaluate_fitness(self, chromosomes):
        pass

    def run_impl(self, generations, prob_mutate, prob_crossover):
        lenght_of_chromosome = 0
        chromosomesArray = []
        chromosomes = self.get_chromosomes()
        for c in chromosomes:
            if lenght_of_chromosome == 0:
                lenght_of_chromosome = c.num_of_genes
            # Each chromosome's length should be the same
            assert lenght_of_chromosome == c.num_of_genes
            for g in c.dna:
                chromosomesArray += g
            # chromosomesArray += c.dna[0]

        num_of_chromosomes = len(chromosomes)
        distances = numpy.zeros(num_of_chromosomes, dtype=numpy.float32)
        survivors = numpy.zeros(num_of_chromosomes, dtype=numpy.bool)
        np_chromosomes = numpy.array(chromosomesArray, dtype=numpy.int32)

        mf = cl.mem_flags
        # Random number should be given by Host program because OpenCL doesn't have a random number
        # generator. We just include one, Noise.cl.
        rnum = [random.randint(1, (int)(time()))]
        dev_rnum = cl.Buffer(self.ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                             hostbuf=numpy.array(rnum, dtype=numpy.int32))

        best_fit = [sys.maxsize]
        weakest_fit = [0.0]
        dev_best = cl.Buffer(self.ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                             hostbuf=numpy.array(best_fit, dtype=numpy.float32))
        dev_weakest = cl.Buffer(self.ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                hostbuf=numpy.array(weakest_fit, dtype=numpy.float32))

        dev_chromosomes = cl.Buffer(self.ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                    hostbuf=np_chromosomes)
        dev_distances = cl.Buffer(self.ctx, mf.WRITE_ONLY, distances.nbytes)
        dev_survivors = cl.Buffer(self.ctx, mf.WRITE_ONLY, survivors.nbytes)

        cl.enqueue_copy(self.queue, dev_distances, distances)

        exec_evt = None
        for i in range(generations):
            exec_evt = self.prg.ga_one_generation(self.queue,
                                                  (num_of_chromosomes,),
                                                  (num_of_chromosomes,),
                                                  self.dev_points.data,
                                                  dev_chromosomes,
                                                  dev_distances,
                                                  dev_survivors,
                                                  dev_rnum,
                                                  dev_best,
                                                  dev_weakest,
                                                  numpy.int32(len(self.city_points)),
                                                  numpy.int32(num_of_chromosomes),
                                                  numpy.float32(prob_mutate),
                                                  numpy.float32(prob_crossover))
        if exec_evt:
            exec_evt.wait()
        cl.enqueue_read_buffer(self.queue, dev_distances, distances)
        cl.enqueue_read_buffer(self.queue, dev_chromosomes, np_chromosomes).wait()

        minDistance = min(value for value in distances)
        minIndex = list(distances).index(minDistance)
        print("Shortest Length: %f @ %d"%(minDistance, minIndex))

        # We had convert chromosome to a cyclic gene. So, the num_of_genes in CL is more than python
        # by one.
        startGeneId = minIndex * (chromosomes[0].num_of_genes)
        endGeneId = (minIndex + 1) * (chromosomes[0].num_of_genes)
        self.best = [v for v in np_chromosomes[startGeneId:endGeneId]]
        self.best_fitness = minDistance

def run(num_cities, num_chromosomes, generations):
    init_testing_rand_seed()
    city_ids = list(range(1, num_cities + 1))
    city_info = {city_id: (random.random() * 100, random.random() * 100) for city_id in city_ids}

    chromosomes = create_chromosomes_by_shuffling(num_chromosomes, city_ids)

    tsp_ga_cl = TSPGACL(city_info, chromosomes)

    prob_mutate = 0.10
    prob_cross = 0.50
    tsp_ga_cl.run(generations, prob_mutate, prob_cross)

    print("run took", tsp_ga_cl.elapsed_time, "seconds")
    best = tsp_ga_cl.get_best()
    print("Shortest Path: " + " => ".join(str(d) for d in best))
    assert len(set(best)) == num_cities, "Duplicated city in the sequence."

    plot_result(city_info, best)

if __name__ == '__main__':
    cites, chromosomes, gens = get_testing_params()
    run(num_cities=cites, num_chromosomes=chromosomes, generations=gens)
