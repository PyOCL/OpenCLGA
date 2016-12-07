import os
import sys
import time
import random
import numpy
import pyopencl as cl
from abc import ABC, abstractmethod
from chromosome import Chromosome

class OpenCLGA(ABC):
    def __init__(self, sample_chromosome, generations, population, fitness_kernel_str, fitness_func,
                 extra_include_path=[]):
        self.__sample_chromosome = sample_chromosome
        self.__chromosome_type = type(sample_chromosome)
        self.__generations = generations
        self.__population = population
        self.__fitness_function = fitness_func
        self.__fitness_kernel_str = fitness_kernel_str
        self.__best = None
        self.__best_fitness = sys.maxsize
        self.__elapsed_time = None
        self.__init_cl(extra_include_path)
        self.__create_program()

    # public properties
    @property
    def best(self):
        return self.__best

    @property
    def best_fitness(self):
        return self.__best_fitness

    @property
    def elapsed_time(self):
        return self.__elapsed_time

    # private properties
    @property
    def __populate_codes(self):
        ctype = self.__chromosome_type
        return "#define POPULATION_SIZE " + str(self.__population) + "\n" +\
               "#define POPULATE_FUNCTION " + ctype.populate_function + "\n" +\
               "#define CHROMOSOME_TYPE " +  ctype.struct_name + "\n"

    @property
    def __evaluate_code(self):
        ctype = self.__chromosome_type
        return "#define CHROMOSOME_SIZE " + ctype.chromosome_size_define + "\n" +\
               "#define CROSSOVER " + ctype.crossover_function + "\n" +\
               "#define MUTATE " + ctype.mutation_function + "\n" +\
               "#define CALCULATE_FITNESS " + self.__fitness_function + "\n"

    @property
    def __include_code(self):
        sample_gene = self.__sample_chromosome.genes[0]
        gtype = type(sample_gene)
        ctype = self.__chromosome_type
        return self.__sample_chromosome.kernelize() + "\n" +\
               "#include \"" + gtype.kernel_file + "\"\n" +\
               "#include \"" + ctype.kernel_file + "\"\n\n"

    # private methods
    def __init_cl(self, extra_include_path):
        # create OpenCL context, queue, and memory
        self.__ctx = cl.create_some_context()
        self.__queue = cl.CommandQueue(self.__ctx)
        self.__mem_pool =cl.tools.MemoryPool(cl.tools.ImmediateAllocator(self.__queue))
        self.__include_path = []
        paths = extra_include_path + ["cl"]
        for path in paths:
            escapedPath = path.replace(' ', '^ ') if sys.platform.startswith('win')\
                                                  else path.replace(' ', '\\ ')
            # After looking into the source code of pyopencl/__init__.py
            # "-I" and folder path should be sepearetd. And " should not included in string path.
            self.__include_path.append('-I')
            self.__include_path.append(os.path.join(os.getcwd(), escapedPath))

    def __create_program(self):
        codes = self.__populate_codes + "\n" +\
                self.__evaluate_code + "\n" +\
                self.__include_code + "\n" +\
                self.__fitness_kernel_str
        f = open(os.path.join("cl", "ocl_ga.c"), "r")
        fstr = "".join(f.readlines())
        f.close()

        fdbg = open("final.cl", 'w')
        fdbg.write(codes + fstr)
        fdbg.close()
        self.__prg = cl.Program(self.__ctx, codes + fstr).build(self.__include_path);

    def __run_impl(self, prob_mutate, prob_crossover):
        total_dna_size = self.__population * self.__sample_chromosome.dna_total_length

        distances = numpy.zeros(self.__population, dtype=numpy.float32)
        survivors = numpy.zeros(self.__population, dtype=numpy.bool)
        np_chromosomes = numpy.zeros(total_dna_size, dtype=numpy.int32)

        mf = cl.mem_flags
        # Random number should be given by Host program because OpenCL doesn't have a random number
        # generator. We just include one, Noise.cl.
        rnum = [random.randint(1, (int)(time.time()))]
        dev_rnum = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                             hostbuf=numpy.array(rnum, dtype=numpy.int32))

        best_fit = [sys.maxsize]
        weakest_fit = [0.0]
        dev_best = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                             hostbuf=numpy.array(best_fit, dtype=numpy.float32))
        dev_weakest = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                hostbuf=numpy.array(weakest_fit, dtype=numpy.float32))

        dev_chromosomes = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                    hostbuf=np_chromosomes)
        dev_distances = cl.Buffer(self.__ctx, mf.WRITE_ONLY, distances.nbytes)
        dev_survivors = cl.Buffer(self.__ctx, mf.WRITE_ONLY, survivors.nbytes)

        cl.enqueue_copy(self.__queue, dev_distances, distances)

        exec_evt = self.__prg.ocl_ga_populate(self.__queue,
                                            (self.__population,),
                                            (self.__population,),
                                            dev_chromosomes,
                                            dev_rnum)
        for i in range(self.__generations):
            exec_evt = self.__prg.ocl_ga_evaluate(self.__queue,
                                                  (self.__population,),
                                                  (self.__population,),
                                                  dev_chromosomes,
                                                  dev_distances,
                                                  dev_survivors,
                                                  dev_rnum,
                                                  dev_best,
                                                  dev_weakest,
                                                  numpy.float32(prob_mutate),
                                                  numpy.float32(prob_crossover))
        if exec_evt:
            exec_evt.wait()

        cl.enqueue_read_buffer(self.__queue, dev_distances, distances)
        cl.enqueue_read_buffer(self.__queue, dev_chromosomes, np_chromosomes).wait()

        minDistance = min(value for value in distances)
        minIndex = list(distances).index(minDistance)
        print("Shortest Length: %f @ %d"%(minDistance, minIndex))

        # We had convert chromosome to a cyclic gene. So, the num_of_genes in CL is more than python
        # by one.
        startGeneId = minIndex * (self.__sample_chromosome.num_of_genes)
        endGeneId = (minIndex + 1) * (self.__sample_chromosome.num_of_genes)
        self.__best = [v for v in np_chromosomes[startGeneId:endGeneId]]
        self.__best_fitness = minDistance

    # public methods
    def run(self, prob_mutate, prob_crossover):
        # This function is not supposed to be overriden
        assert 0 <= prob_mutate <= 1
        assert 0 <= prob_crossover <= 1
        start_time = time.time()
        self.__run_impl(prob_mutate, prob_crossover)
        self.__elapsed_time = time.time() - start_time
