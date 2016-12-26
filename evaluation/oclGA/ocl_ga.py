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
                 fitness_args, extra_include_path=[]):
        self.__sample_chromosome = sample_chromosome
        self.__chromosome_type = type(sample_chromosome)
        self.__generations = generations
        self.__population = population
        self.__fitness_function = fitness_func
        self.__fitness_kernel_str = fitness_kernel_str
        self.__fitness_args = fitness_args
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
        fit_args = ", ".join(["global " + v["t"] + "* _f_" + v["n"] for v in self.__fitness_args])
        fit_argv = ", ".join(["_f_" + v["n"] for v in self.__fitness_args])
        if len(fit_args) > 0:
            fit_args = ", " + fit_args
            fit_argv = ", " + fit_argv

        return "#define CHROMOSOME_SIZE " + ctype.chromosome_size_define + "\n" +\
               "#define CALCULATE_FITNESS " + self.__fitness_function + "\n"+\
               "#define FITNESS_ARGS " + fit_args + "\n"+\
               "#define FITNESS_ARGV " + fit_argv + "\n"

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

    def __type_to_numpy_type(self, t):
        if t == "float":
            return numpy.float32
        elif t == "int":
            return numpy.int32
        else:
            raise "unsupported python type"

    def __run_impl(self, prob_mutate, prob_crossover):
        ctype = self.__chromosome_type
        total_dna_size = self.__population * self.__sample_chromosome.dna_total_length

        distances = numpy.zeros(self.__population, dtype=numpy.float32)
        np_chromosomes = numpy.zeros(total_dna_size, dtype=numpy.int32)

        mf = cl.mem_flags
        # Random number should be given by Host program because OpenCL doesn't have a random number
        # generator. We just include one, Noise.cl.
        rnum = [random.randint(0, 4294967295) for i in range(self.__population)]
        ## note: numpy.random.rand() gives us a list float32 and we cast it to uint32 at the calling
        ##       of kernel function. It just views the original byte order as uint32.
        dev_rnum = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                             hostbuf=numpy.array(rnum, dtype=numpy.uint32))
        dev_chromosomes = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                    hostbuf=np_chromosomes)
        dev_distances = cl.Buffer(self.__ctx, mf.WRITE_ONLY, distances.nbytes)

        fitness_args = [dev_chromosomes, dev_distances]

        ## create buffers for fitness arguments
        for arg in self.__fitness_args:
            fitness_args.append(cl.Buffer(self.__ctx, mf.READ_ONLY | mf.COPY_HOST_PTR,
                          hostbuf=numpy.array(arg["v"], dtype=self.__type_to_numpy_type(arg["t"]))))

        cl.enqueue_copy(self.__queue, dev_distances, distances)

        ## call preexecute_kernels for internal data structure preparation
        self.__sample_chromosome.preexecute_kernels(self.__ctx, self.__queue, self.__population)

        ## populate the first generation
        exec_evt = self.__prg.ocl_ga_populate(self.__queue,
                                              (self.__population,),
                                              (self.__population,),
                                              dev_chromosomes,
                                              dev_rnum).wait()
        exec_evt = self.__prg.ocl_ga_calculate_fitness(self.__queue,
                                                       (self.__population,),
                                                       (self.__population,),
                                                       *fitness_args).wait()
        ## start the evolution
        for i in range(self.__generations):
            self.__sample_chromosome.execute_crossover(self.__prg,
                                                       self.__queue,
                                                       self.__population,
                                                       i,
                                                       prob_crossover,
                                                       dev_chromosomes,
                                                       dev_distances,
                                                       dev_rnum)
            self.__sample_chromosome.execute_mutation(self.__prg,
                                                      self.__queue,
                                                      self.__population,
                                                      i,
                                                      prob_mutate,
                                                      dev_chromosomes,
                                                      dev_distances,
                                                      dev_rnum)
            self.__prg.ocl_ga_calculate_fitness(self.__queue,
                                                (self.__population,),
                                                (self.__population,),
                                                *fitness_args).wait()

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
