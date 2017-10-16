#!/usr/bin/python3
import math
import numpy
import os
import pyopencl as cl
import random
import sys
from OpenCLGA import utils

class AntTSP():

    def __init__(self, options):
        self.__iterations = options['iterations']
        self.__ants = options['ants']
        # the option for pheromone affecting probability
        self.__alpha = options['alpha']
        # the option for length affecting probability
        self.__beta = options['beta']
        # node should be an array of object. The structure of object should be
        # 1. x: the position of x a float
        # 2. y: the position of y a float
        self.__nodes = options['nodes']
        self.__node_count = len(self.__nodes)
        self.__matrix_size = self.__node_count * self.__node_count
        # the option for pheromone evaporating
        self.__evaporation = options['evaporation']
        # the option for leaking pheromone
        self.__q = options['q']
        self.__best_result = None
        self.__best_fitness = sys.float_info.max

        self.__init_cl()
        self.__create_program()

    def __init_cl(self, cl_context=None):
        self.__ctx = cl_context if cl_context is not None else cl.create_some_context()
        self.__queue = cl.CommandQueue(self.__ctx)

    def __create_program(self):
        f = open('ant_tsp.cl', 'r');
        fstr = ''.join(f.readlines())
        f.close()
        ocl_kernel_path = os.path.join(os.path.dirname(os.path.abspath('../../' + __file__)), 'kernel').replace(' ', '\\ ')
        options = [
            '-D', 'ANT_COUNT={}'.format(self.__ants),
            '-D', 'NODE_COUNT={}'.format(self.__node_count),
            '-D', 'ALPHA={}'.format(self.__alpha),
            '-D', 'BETA={}'.format(self.__beta),
            '-D', 'EVAPORATION={}'.format(self.__evaporation),
            '-D', 'Q={}'.format(self.__q),
            '-I', ocl_kernel_path
        ]
        self.__prg = cl.Program(self.__ctx, fstr).build(options);

    def __prepare_cl_buffers(self):
        mf = cl.mem_flags
        # prepare distances buffers
        self.__path_distances = numpy.zeros(shape=[self.__node_count, self.__node_count],
                                           dtype=numpy.float32)

        self.__dev_path_distances = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                              hostbuf=self.__path_distances)

        # initialize all pheromones of paths with 1
        self.__path_pheromones = numpy.empty(shape=[self.__node_count, self.__node_count],
                                             dtype=numpy.float32)
        self.__path_pheromones.fill(1)
        self.__dev_path_pheromones = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                               hostbuf=self.__path_pheromones)

        # prepare buffers for node position: x, y
        x = numpy.empty(self.__node_count, dtype=numpy.float32)
        y = numpy.empty(self.__node_count, dtype=numpy.float32)
        for i in range(self.__node_count):
            x[i] = self.__nodes[i][0]
            y[i] = self.__nodes[i][1]

        self.__dev_x = cl.Buffer(self.__ctx, mf.READ_ONLY | mf.COPY_HOST_PTR,
                                 hostbuf=x)
        self.__dev_y = cl.Buffer(self.__ctx, mf.READ_ONLY | mf.COPY_HOST_PTR,
                                 hostbuf=y)

        # Random number should be given by Host program because OpenCL doesn't have a random number
        # generator. We just include one, Noise.cl.
        rnum = [random.randint(0, 4294967295) for i in range(self.__ants)]
        ## note: numpy.random.rand() gives us a list float32 and we cast it to uint32 at the calling
        ##       of kernel function. It just views the original byte order as uint32.
        self.__dev_rnum = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                    hostbuf=numpy.array(rnum, dtype=numpy.uint32))

        # we should prepare buffer memory for each ant on each node.
        buffer_size = 4 * self.__node_count * self.__ants
        # the visited_nodes is used for storing the path of an ant.
        self.__dev_visited_nodes = cl.Buffer(self.__ctx, mf.READ_WRITE, buffer_size)
        # the path_probabilities is used for choosing next node
        self.__dev_path_probabilities = cl.Buffer(self.__ctx, mf.READ_WRITE, buffer_size)
        # the tmp pheromones is used for calcuating probabilities for next node
        self.__dev_tmp_pheromones = cl.Buffer(self.__ctx, mf.READ_WRITE, buffer_size)
        # this is for keepting fitness value of each ant at a single round.
        self.__dev_ant_fitnesses = cl.Buffer(self.__ctx, mf.READ_WRITE, 4 * self.__ants)

    def __calculate_distances(self):
        # calculate the distances betwen two points.
        self.__prg.ant_tsp_calculate_distances(self.__queue,
                                               (self.__node_count, self.__node_count),
                                               (1, 1),
                                               self.__dev_x,
                                               self.__dev_y,
                                               self.__dev_path_distances)

    def __execute_single_generation(self, generation):
        self.__prg.ant_tsp_run_ant(self.__queue,
                                   (self.__ants, ),
                                   (1, ),
                                   self.__dev_visited_nodes,
                                   self.__dev_path_probabilities,
                                   self.__dev_tmp_pheromones,
                                   self.__dev_path_pheromones,
                                   self.__dev_path_distances,
                                   self.__dev_ant_fitnesses,
                                   self.__dev_rnum).wait()

        visited_nodes = numpy.empty(self.__ants * self.__node_count, dtype=numpy.int32)
        fitnesses = numpy.empty(self.__ants, dtype=numpy.float32)
        cl.enqueue_copy(self.__queue, visited_nodes, self.__dev_visited_nodes)
        cl.enqueue_copy(self.__queue, fitnesses, self.__dev_ant_fitnesses).wait();

        best_index = -1;
        best_fitness = sys.float_info.max
        for index, fitness in enumerate(fitnesses):
            if fitness < best_fitness:
                best_index = index
                best_fitness = fitness

        start_index = best_index * self.__node_count
        end_index = (best_index + 1) * self.__node_count
        best_result = visited_nodes[start_index:end_index]


        # update path_pheromones
        self.__prg.ant_tsp_evaporate_pheromones(self.__queue,
                                                (self.__node_count, self.__node_count),
                                                (1, 1),
                                                self.__dev_path_pheromones)

        self.__prg.ant_tsp_update_pheromones(self.__queue,
                                             (self.__node_count, self.__node_count),
                                             (1, 1),
                                             self.__dev_visited_nodes,
                                             self.__dev_ant_fitnesses,
                                             self.__dev_path_pheromones).wait()
        return (best_result, best_fitness)

    def run(self):
        self.__prepare_cl_buffers()
        self.__calculate_distances()
        for generation in range(self.__iterations):
            result = self.__execute_single_generation(generation)
            print('best fitness #{}: {}'.format(generation, result[1]))
            if result[1] < self.__best_fitness:
                self.__best_fitness = result[1]
                self.__best_result = result[0]

        return (self.__best_result, self.__best_fitness)

if __name__ == '__main__':
    random.seed(1)
    city_info = { city_id: (random.random() * 100, random.random() * 100) for city_id in range(30) }
    print('cities:')
    print(city_info)
    ant = AntTSP({
        'iterations': 100,
        'ants': 10000,
        'alpha': 1.1,
        'beta': 1.5,
        'evaporation': 0.85,
        'q': 10000,
        'nodes': city_info
    })

    result = ant.run()
    print('Length: {}'.format(result[1]))
    print('Shortest Path: ' + ' => '.join(str(g) for g in result[0]))
    utils.plot_tsp_result(city_info, result[0])
