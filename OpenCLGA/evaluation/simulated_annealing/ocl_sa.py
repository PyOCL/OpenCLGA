#!/usr/bin/python3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from abc import ABCMeta
from utils import calc_linear_distance, plot_tsp_result, plot_grouping_result
import math
import numpy
import random
import pyopencl as cl

from sa import SimulatedAnnealing, TSPSolution

class OclTSPSolution(TSPSolution):
    def __init__(self, city_info):
        TSPSolution.__init__(self, city_info)

        self.size_of_solution = len(city_info.keys())
        self.num_of_solutions = 100

    @property
    def elements_kernel_str(self):
        # Chromosome can use this function to declare elements array
        elements_str = ', '.join([str(v) for v in list(self.city_info.keys())])
        return '{' + elements_str + '}\n'

    def kernelize(self):
        candidates = '#define ELEMENT_SPACE ' + self.elements_kernel_str + '\n'
        populats = '#define NUM_OF_SOLUTION ' + str(self.num_of_solutions) + '\n'
        defines = '#define SOLUTION_SIZE ' + str(self.size_of_solution) + '\n'
        return candidates + populats + defines

    def get_solution_info(self):
        self.__np_solution = numpy.zeros(self.size_of_solution * self.num_of_solutions, dtype=numpy.int32)
        return self.num_of_solutions, self.__np_solution

    def get_cost_buffer(self):
        self.__np_costs = numpy.zeros(self.num_of_solutions, dtype=numpy.float32)
        return self.__np_costs

    def create_internal_buffer(self, ctx):
        cityxy = [(self.city_info[idx][0], self.city_info[idx][1]) for idx in range(len(self.city_info))]
        self.__np_cityxy = numpy.array(cityxy, dtype=numpy.float32)

        mf = cl.mem_flags

        self.__dev_cityxy = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                      hostbuf=self.__np_cityxy)

        self.__dev_cityxy = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                      hostbuf=self.__np_cityxy)

        self.__np_iterations = numpy.int32(self.iterations)
        self.__np_temperature = numpy.float32(self.temperature)
        self.__np_terminate_temperature = numpy.float32(self.terminate_temperature)
        self.__np_alpha = numpy.float32(self.alpha)

    def anneal(self, prog, queue, rand, solutions, costs):
        prog.ocl_sa_populate_solutions(queue,
                                       (self.num_of_solutions,),
                                       (1,),
                                       self.__np_iterations,
                                       self.__np_temperature,
                                       self.__np_terminate_temperature,
                                       self.__np_alpha,
                                       solutions,
                                       rand,
                                       self.__dev_cityxy,
                                       costs).wait()

        cl.enqueue_copy(queue, self.__np_solution, solutions).wait()
        cl.enqueue_copy(queue, self.__np_costs, costs).wait()
        self.plot_best_solution()

    def plot_best_solution(self):
        min_cost = float('inf')
        min_idx = 0
        for idx, cost in enumerate(self.__np_costs):
            if cost < min_cost:
                min_cost = cost
                min_idx = idx

        solution = self.__np_solution[min_idx*self.size_of_solution:(min_idx+1)*self.size_of_solution]
        plot_tsp_result(self.city_info, solution)

    def plot_all_solutions(self):
        for i in range(self.num_of_solutions):
            solution = []
            if i == self.num_of_solutions - 1:
                solution = self.__np_solution[i * self.size_of_solution:]
            else:
                solution = self.__np_solution[i * self.size_of_solution:(i+1) * self.size_of_solution]
            plot_tsp_result(self.city_info, solution)

class OpenCLSA(SimulatedAnnealing):
    def __init__(self, cls_solution, options):
        SimulatedAnnealing.__init__(self, cls_solution)

        extra_path = options.get('extra_include_path', [])
        cl_context = options.get('cl_context', None)

        self.__debug_mode = True
        self.__init_cl(cl_context, extra_path)
        self.__create_program()
        self.__init_cl_member()
        pass

    def __init_cl(self, cl_context, extra_include_path):
        # create OpenCL context, queue, and memory
        # NOTE: Please set PYOPENCL_CTX=N (N is the device number you want to use)
        #       at first if it's in external_process mode, otherwise a exception
        #       will be thrown, since it's not in interactive mode.
        # TODO: Select a reliable device during runtime by default.
        self.__ctx = cl_context if cl_context is not None else cl.create_some_context()
        self.__queue = cl.CommandQueue(self.__ctx)
        self.__include_path = []

        ocl_kernel_path = os.path.join(os.path.dirname(os.path.abspath('../../' + __file__)), 'kernel').replace(' ', '\\ ')
        paths = extra_include_path + [ocl_kernel_path]
        for path in paths:
            escapedPath = path.replace(' ', '^ ') if sys.platform.startswith('win')\
                                                  else path.replace(' ', '\\ ')
            # After looking into the source code of pyopencl/__init__.py
            # '-I' and folder path should be sepearetd. And ' should not included in string path.
            self.__include_path.append('-I')
            self.__include_path.append(os.path.join(os.getcwd(), escapedPath))

    def __create_program(self):
        self.__include_code = self.sas.kernelize()
        codes = self.__include_code + '\n'
        # codes = self.__args_codes + '\n' +\
        #         self.__populate_codes + '\n' +\
        #         self.__evaluate_code + '\n' +\
        #         self.__include_code + '\n' +\
        #         self.__fitness_kernel_str

        f = open('ocl_sa.cl', 'r')
        fstr = ''.join(f.readlines())
        f.close()

        if self.__debug_mode:
            fdbg = open('final.cl', 'w')
            fdbg.write(codes + fstr)
            fdbg.close()

        self.__prg = cl.Program(self.__ctx, codes + fstr).build(self.__include_path);

    def __init_cl_member(self):
        self.__np_costs = self.sas.get_cost_buffer()
        num_of_solution, self.__np_solution = self.sas.get_solution_info()

        mf = cl.mem_flags

        # Random number should be given by Host program because OpenCL doesn't have a random number
        # generator. We just include one, Noise.cl.
        rnum = [random.randint(0, 4294967295) for i in range(num_of_solution)]
        ## note: numpy.random.rand() gives us a list float32 and we cast it to uint32 at the calling
        ##       of kernel function. It just views the original byte order as uint32.
        self.__dev_rnum = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                    hostbuf=numpy.array(rnum, dtype=numpy.uint32))

        self.__dev_costs = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                     hostbuf=self.__np_costs)
        self.__dev_solution = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                        hostbuf=self.__np_solution)

        self.sas.create_internal_buffer(self.__ctx)

    ## To save the annealing state
    def save(self):
        pass

    ## To restore the annealing state
    def restore(self):
        pass

    ## Start annealing
    def anneal(self):
        self.sas.anneal(self.__prg,
                        self.__queue,
                        self.__dev_rnum,
                        self.__dev_solution,
                        self.__dev_costs)

        pass

if __name__ == '__main__':
    sa = OpenCLSA(OclTSPSolution, {})
    sa.anneal()