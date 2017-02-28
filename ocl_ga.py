#! /usr/bin/python3

import os
import sys
import time
import random
import numpy
import pickle
import pyopencl as cl

class OpenCLGA():
    def __init__(self, options):
        self.__init_members(options)
        extra_path = options["extra_include_path"] if "extra_include_path" in options else []
        cl_context = options["cl_context"] if "cl_context" in options else None
        self.__init_cl(cl_context, extra_path)
        self.__create_program()

    # public properties
    @property
    def paused(self):
        return self.__paused

    @property
    def elapsed_time(self):
        return self.__elapsed_time

    # private properties
    @property
    def __args_codes(self):
        opt_for_max = 0 if self.__opt_for_max == "min" else 1
        return "#define OPTIMIZATION_FOR_MAX " + str(opt_for_max) + "\n"

    @property
    def __populate_codes(self):
        return "#define POPULATION_SIZE " + str(self.__population) + "\n" +\
               "#define CHROMOSOME_TYPE " +  self.__sample_chromosome.struct_name + "\n"

    @property
    def __evaluate_code(self):
        chromosome = self.__sample_chromosome
        if self.__fitness_args is not None:
            fit_args = ", ".join(["global " + v["t"] + "* _f_" + v["n"] for v in self.__fitness_args])
            fit_argv = ", ".join(["_f_" + v["n"] for v in self.__fitness_args])
            if len(fit_args) > 0:
                fit_args = ", " + fit_args
                fit_argv = ", " + fit_argv
        else:
            fit_args = ""
            fit_argv = ""

        return "#define CHROMOSOME_SIZE " + chromosome.chromosome_size_define + "\n" +\
               "#define CALCULATE_FITNESS " + self.__fitness_function + "\n" +\
               "#define FITNESS_ARGS " + fit_args + "\n"+\
               "#define FITNESS_ARGV " + fit_argv + "\n"

    @property
    def __include_code(self):
        sample_gene = self.__sample_chromosome.genes[0]
        return self.__sample_chromosome.kernelize() + "\n" +\
               "#include \"" + sample_gene.kernel_file + "\"\n" +\
               "#include \"" + self.__sample_chromosome.kernel_file + "\"\n\n"

    # private methods
    def __init_members(self, options):
        self.__sample_chromosome = options["sample_chromosome"]
        self.__termination = options["termination"]
        self.__population = options["population"]
        self.__opt_for_max = options["opt_for_max"] if "opt_for_max" in options else "max"
        self.__np_chromosomes = None
        self.__fitness_function = options["fitness_func"]
        self.__fitness_kernel_str = options["fitness_kernel_str"]
        self.__fitness_args = options["fitness_args"] if "fitness_args" in options else None

        # { gen : {"best":  best_fitness,
        #          "worst": worst_fitness,
        #          "avg":   avg_fitness},
        #  "avg_time_per_gen": avg. elapsed time per generation}
        self.__dictStatistics = {}

        # Generally in GA, it depends on the problem to treat the maximal fitness
        # value as the best or to treat the minimal fitness value as the best.
        self.__fitnesses = numpy.zeros(self.__population, dtype=numpy.float32)
        self.__elapsed_time = 0
        self.__paused = False
        self.__forceStop = False;
        self.__generation_index = 0
        self.__generation_time_diff = 0
        self.__debug_mode = "debug" in options
        self.__generation_callback = options["generation_callback"]\
                                        if "generation_callback" in options else None

    def __init_cl(self, cl_context, extra_include_path):
        # create OpenCL context, queue, and memory
        # NOTE: Please set PYOPENCL_CTX=N (N is the device number you want to use)
        #       at first if it"s in external_process mode, otherwise a exception
        #       will be thrown, since it"s not in interactive mode.
        # TODO: Select a reliable device during runtime by default.
        self.__ctx = cl_context if cl_context is not None else cl.create_some_context()
        self.__queue = cl.CommandQueue(self.__ctx)
        self.__include_path = []
        kernel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kernel")
        paths = extra_include_path + [kernel_path]
        for path in paths:
            escapedPath = path.replace(" ", "^ ") if sys.platform.startswith("win")\
                                                  else path.replace(" ", "\\ ")
            # After looking into the source code of pyopencl/__init__.py
            # "-I" and folder path should be sepearetd. And " should not included in string path.
            self.__include_path.append("-I")
            self.__include_path.append(os.path.join(os.getcwd(), escapedPath))

    def __create_program(self):
        codes = self.__args_codes + "\n" +\
                self.__populate_codes + "\n" +\
                self.__evaluate_code + "\n" +\
                self.__include_code + "\n" +\
                self.__fitness_kernel_str
        kernel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kernel")
        f = open(os.path.join(kernel_path, "ocl_ga.c"), "r")
        fstr = "".join(f.readlines())
        f.close()
        if self.__debug_mode:
            fdbg = open("final.cl", "w")
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

    def __dump_kernel_info(self, prog, ctx, chromosome_wrapper, device = None):
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        import utils
        utils.calculate_estimated_kernel_usage(prog,
                                               ctx,
                                               chromosome_wrapper.get_populate_kernel_names())
        utils.calculate_estimated_kernel_usage(prog,
                                               ctx,
                                               ["ocl_ga_calculate_fitness"])
        utils.calculate_estimated_kernel_usage(prog,
                                               ctx,
                                               chromosome_wrapper.get_crossover_kernel_names())
        utils.calculate_estimated_kernel_usage(prog,
                                               ctx,
                                               chromosome_wrapper.get_mutation_kernel_names())

    def __preexecute_kernels(self):
        total_dna_size = self.__population * self.__sample_chromosome.dna_total_length

        self.__fitnesses = numpy.zeros(self.__population, dtype=numpy.float32)
        self.__np_chromosomes = numpy.zeros(total_dna_size, dtype=numpy.int32)

        mf = cl.mem_flags
        # Random number should be given by Host program because OpenCL doesn't have a random number
        # generator. We just include one, Noise.cl.
        rnum = [random.randint(0, 4294967295) for i in range(self.__population)]
        ## note: numpy.random.rand() gives us a list float32 and we cast it to uint32 at the calling
        ##       of kernel function. It just views the original byte order as uint32.
        self.__dev_rnum = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                             hostbuf=numpy.array(rnum, dtype=numpy.uint32))

        self.__dev_chromosomes = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                    hostbuf=self.__np_chromosomes)
        self.__dev_fitnesses = cl.Buffer(self.__ctx, mf.WRITE_ONLY, self.__fitnesses.nbytes)

        self.__fitness_args_list = [self.__dev_chromosomes, self.__dev_fitnesses]

        if self.__fitness_args is not None:
            ## create buffers for fitness arguments
            for arg in self.__fitness_args:
                self.__fitness_args_list.append(cl.Buffer(self.__ctx,
                                                     mf.READ_ONLY | mf.COPY_HOST_PTR,
                                                     hostbuf=numpy.array(arg["v"],
                                                     dtype=self.__type_to_numpy_type(arg["t"]))))

        cl.enqueue_copy(self.__queue, self.__dev_fitnesses, self.__fitnesses)

        ## call preexecute_kernels for internal data structure preparation
        self.__sample_chromosome.preexecute_kernels(self.__ctx, self.__queue, self.__population)

        ## dump information on kernel resources usage
        self.__dump_kernel_info(self.__prg, self.__ctx, self.__sample_chromosome)

    def __populate_first_generations(self, prob_mutate, prob_crossover):
        ## populate the first generation
        self.__sample_chromosome.execute_populate(self.__prg,
                                                  self.__queue,
                                                  self.__population,
                                                  self.__dev_chromosomes,
                                                  self.__dev_rnum)

        self.__prg.ocl_ga_calculate_fitness(self.__queue,
                                            (self.__population,),
                                            (1,),
                                            *self.__fitness_args_list).wait()

    def __execute_single_generation(self, index, prob_mutate, prob_crossover):
        self.__sample_chromosome.execute_crossover(self.__prg,
                                                   self.__queue,
                                                   self.__population,
                                                   index,
                                                   prob_crossover,
                                                   self.__dev_chromosomes,
                                                   self.__dev_fitnesses,
                                                   self.__dev_rnum)
        self.__sample_chromosome.execute_mutation(self.__prg,
                                                  self.__queue,
                                                  self.__population,
                                                  index,
                                                  prob_mutate,
                                                  self.__dev_chromosomes,
                                                  self.__dev_fitnesses,
                                                  self.__dev_rnum)

        self.__prg.ocl_ga_calculate_fitness(self.__queue,
                                            (self.__population,),
                                            (1,),
                                            *self.__fitness_args_list).wait()
        self.__dictStatistics[index] = {}
        self.__dictStatistics[index]["best"] = self.__sample_chromosome.get_current_best()
        self.__dictStatistics[index]["worst"] = self.__sample_chromosome.get_current_worst()
        self.__dictStatistics[index]["avg"] = self.__sample_chromosome.get_current_avg()
        if self.__generation_callback is not None:
            self.__generation_callback(index, self.__dictStatistics[index])

    def __evolve_by_count(self, count, prob_mutate, prob_crossover):
        start_time = time.time()
        for i in range(self.__generation_index, count):
            self.__execute_single_generation(i, prob_mutate, prob_crossover)
            if self.__sample_chromosome.early_terminated:
                break

            if self.__paused:
                self.__generation_index = i + 1
                self.__generation_time_diff = time.time() - start_time
                cl.enqueue_read_buffer(self.__queue, self.__dev_fitnesses, self.__fitnesses)
                cl.enqueue_read_buffer(self.__queue, self.__dev_chromosomes, self.__np_chromosomes).wait()
                break
            if self.__forceStop:
                cl.enqueue_read_buffer(self.__queue, self.__dev_fitnesses, self.__fitnesses)
                cl.enqueue_read_buffer(self.__queue, self.__dev_chromosomes, self.__np_chromosomes).wait()
                break

    def __evolve_by_time(self, max_time, prob_mutate, prob_crossover):
        start_time = time.time()
        while True:
            self.__execute_single_generation(self.__generation_index, prob_mutate, prob_crossover)
            # calculate elapsed time
            elapsed_time = time.time() - start_time + self.__generation_time_diff
            self.__generation_index = self.__generation_index + 1
            if self.__sample_chromosome.early_terminated or elapsed_time > max_time:
                break

            if self.__paused:
                self.__generation_time_diff = time.time() - start_time
                cl.enqueue_read_buffer(self.__queue, self.__dev_fitnesses, self.__fitnesses)
                cl.enqueue_read_buffer(self.__queue, self.__dev_chromosomes, self.__np_chromosomes).wait()
                break
            if self.__forceStop:
                cl.enqueue_read_buffer(self.__queue, self.__dev_fitnesses, self.__fitnesses)
                cl.enqueue_read_buffer(self.__queue, self.__dev_chromosomes, self.__np_chromosomes).wait()
                break

    def __start_evolution(self, prob_mutate, prob_crossover):
        generation_start = time.time()
        ## start the evolution
        if self.__termination["type"] == "time":
            self.__evolve_by_time(self.__termination["time"], prob_mutate, prob_crossover)
        elif self.__termination["type"] == "count":
            self.__evolve_by_count(self.__termination["count"], prob_mutate, prob_crossover)

        if self.__paused:
            return;

        cl.enqueue_read_buffer(self.__queue, self.__dev_fitnesses, self.__fitnesses)
        cl.enqueue_read_buffer(self.__queue, self.__dev_chromosomes, self.__np_chromosomes).wait()

        total_time_consumption = time.time() - generation_start + self.__generation_time_diff
        avg_time_per_gen = total_time_consumption / float(len(self.__dictStatistics))
        self.__dictStatistics["avg_time_per_gen"] = avg_time_per_gen

    def __save_state(self, data):
        # save data from intenal struct
        data["generation_idx"] = self.__generation_index
        data["statistics"] = self.__dictStatistics
        data["generation_time_diff"] = self.__generation_time_diff
        data["population"] = self.__population

        # read data from kernel
        rnum = numpy.zeros(self.__population, dtype=numpy.float32)
        cl.enqueue_read_buffer(self.__queue, self.__dev_rnum, rnum)
        cl.enqueue_read_buffer(self.__queue, self.__dev_fitnesses, self.__fitnesses)
        cl.enqueue_read_buffer(self.__queue, self.__dev_chromosomes, self.__np_chromosomes).wait()
        # save kernel memory to data
        data["rnum"] = rnum
        data["fitnesses"] = self.__fitnesses
        data["chromosomes"] = self.__np_chromosomes

        self.__sample_chromosome.save(data, self.__ctx, self.__queue, self.__population)

    def __restore_state(self, data):
        self.__generation_index = data["generation_idx"]
        self.__dictStatistics = data["statistics"]
        self.__generation_time_diff = data["generation_time_diff"]
        self.__population = data["population"]

        rnum = data["rnum"]
        self.__fitnesses = data["fitnesses"]
        self.__np_chromosomes = data["chromosomes"]
        # restore CL variables
        mf = cl.mem_flags
        self.__dev_rnum = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                             hostbuf=numpy.array(rnum, dtype=numpy.uint32))
        self.__dev_chromosomes = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                    hostbuf=self.__np_chromosomes)
        self.__dev_fitnesses = cl.Buffer(self.__ctx, mf.WRITE_ONLY, self.__fitnesses.nbytes)
        self.__fitness_args_list = [self.__dev_chromosomes, self.__dev_fitnesses]
        if self.__fitness_args is not None:
            ## create buffers for fitness arguments
            for arg in self.__fitness_args:
                self.__fitness_args_list.append(cl.Buffer(self.__ctx,
                                                     mf.READ_ONLY | mf.COPY_HOST_PTR,
                                                     hostbuf=numpy.array(arg["v"],
                                                     dtype=self.__type_to_numpy_type(arg["t"]))))
        # Copy data from main memory to GPU memory
        cl.enqueue_copy(self.__queue, self.__dev_fitnesses, self.__fitnesses)
        cl.enqueue_copy(self.__queue, self.__dev_chromosomes, self.__np_chromosomes)
        cl.enqueue_copy(self.__queue, self.__dev_rnum, rnum).wait()

        self.__sample_chromosome.restore(data, self.__ctx, self.__queue, self.__population)

    # public methods
    def prepare(self):
        self.__preexecute_kernels()

    def run(self, prob_mutate, prob_crossover):
        # This function is not supposed to be overriden
        assert 0 <= prob_mutate <= 1
        assert 0 <= prob_crossover <= 1
        start_time = time.time()
        if not self.__paused:
            self.__populate_first_generations(prob_mutate, prob_crossover)

        self.__paused = False
        self.__start_evolution(prob_mutate, prob_crossover)
        self.__elapsed_time += time.time() - start_time

    def stop(self):
        self.__forceStop = True

    def pause(self):
        self.__paused = True

    def save(self, filename):
        assert self.__paused, "save is only availabled while paused"
        data = dict()
        self.__save_state(data)
        f = open(filename, "wb")
        pickle.dump(data, f)
        f.close()

    def restore(self, filename):
        f = open(filename, "rb")
        data = pickle.load(f)
        f.close()
        self.__restore_state(data)

    def get_statistics(self):
        return self.__dictStatistics

    def get_the_best(self):
        assert self.__opt_for_max in ["max", "min"]

        best_fitness = eval(self.__opt_for_max)(value for value in self.__fitnesses)
        best_index = list(self.__fitnesses).index(best_fitness)

        # We had convert chromosome to a cyclic gene. So, the num_of_genes in CL is more than python
        # by one.
        startGeneId = best_index * (self.__sample_chromosome.num_of_genes)
        endGeneId = (best_index + 1) * (self.__sample_chromosome.num_of_genes)
        best = [v for v in self.__np_chromosomes[startGeneId:endGeneId]]
        return best, best_fitness, self.__sample_chromosome.from_kernel_value(best)
