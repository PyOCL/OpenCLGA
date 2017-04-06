#!/usr/bin/python3
import os
import sys
import time
import random
import numpy
import pickle
import pyopencl as cl

from . import utils
from .utilities.generaltaskthread import TaskThread, Task, Logger

class EnterExit(object):
    def __call__(self, func):
        def wrapper(parent, *args, **kwargs):
            parent.state_machine.next(func.__name__)
            func(parent, *args, **kwargs)
            parent.state_machine.next('done')
            # TODO : May send state information back to UI here.
        return wrapper

class StateMachine(Logger):
    # (current state, action) : (next state)
    TRANSITION_TABLE = {
    ('waiting', 'prepare')  : ('preparing'),
    ('waiting', 'restore')  : ('restoring'),
    ('preparing', 'done')   : ('prepared'),
    ('prepared', 'run')     : ('running'),
    ('restoring', 'done')   : ('prepared'),
    ('running', 'pause')    : ('pausing'),
    ('running', 'stop')     : ('stopping'),
    ('pausing', 'done')     : ('paused'),
    ('paused', 'run')       : ('running'),
    ('paused', 'stop')      : ('stopping'),
    ('paused', 'save')      : ('saving'),
    ('stopping', 'done')    : ('stopped'),
    ('saving', 'done')      : ('paused'),
    }
    def __init__(self, openclga, init_state):
        Logger.__init__(self)
        self.openclga = openclga
        self.__curr_state = init_state

    def next(self, action):
        next_state = None
        for k, v in StateMachine.TRANSITION_TABLE.items():
            if self.__curr_state == k[0] and action == k[1]:
                assert next_state is None
                next_state = v
        if next_state is None:
            return
        last_state = self.__curr_state
        self.__curr_state = next_state
        self.info("Change State : {} => {}".format(last_state, next_state))
        if self.openclga.action_callbacks and "state" in self.openclga.action_callbacks:
            self.openclga.action_callbacks["state"](next_state)

class GARun(Task):
    # Iterating GA generation in a separated thread.
    def __init__(self, ga, prob_mutation, prob_crossover):
        Task.__init__(self)
        self.ga = ga
        self.prob_m = prob_mutation
        self.prob_c = prob_crossover
        pass

    def run(self):
        start_time = time.time()
        # We only need to populate first generation at first time, not paused and not restored
        if not self.ga._paused:
            self.ga._populate_first_generations(self.prob_m, self.prob_c)
        self.ga._paused = False
        self.ga._start_evolution(self.prob_m, self.prob_c)
        self.ga._elapsed_time += time.time() - start_time
        if self.ga.action_callbacks and 'run' in self.ga.action_callbacks:
            self.ga.action_callbacks['run'](self.ga._paused)

class OpenCLGA():
    def __init__(self, options, action_callbacks = {}):
        # action_callback
        # - A callback function to send execution status back to ocl_ga_worker.
        #  TODO : Could define to call specific callback according to state.
        if action_callbacks is not None:
            for action, cb in action_callbacks.items():
                assert callable(cb)
        self.state_machine = StateMachine(self, 'waiting')
        self.__init_members(options)
        extra_path = options.get("extra_include_path", [])
        cl_context = options.get("cl_context", None)
        self.__init_cl(cl_context, extra_path)
        self.__create_program()
        self.action_callbacks = action_callbacks

    # public properties
    @property
    def paused(self):
        return self._paused

    @property
    def elapsed_time(self):
        return self._elapsed_time

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
        self.thread = TaskThread(name="GARun")
        self.thread.daemon = True
        self.thread.start()

        self.__sample_chromosome = options["sample_chromosome"]
        self.__termination = options["termination"]
        self.__population = options["population"]
        self.__opt_for_max = options.get("opt_for_max", "max")
        self.__np_chromosomes = None
        self.__fitness_function = options["fitness_func"]
        self.__fitness_kernel_str = options["fitness_kernel_str"]
        self.__fitness_args = options.get("fitness_args", None)

        self.__saved_filename = options.get("saved_filename", None)
        self.__prob_mutation = options.get("prob_mutation", 0)
        self.__prob_crossover = options.get("prob_crossover", 0)
        # { gen : {"best":  best_fitness,
        #          "worst": worst_fitness,
        #          "avg":   avg_fitness},
        #  "avg_time_per_gen": avg. elapsed time per generation}
        self.__dictStatistics = {}

        # Generally in GA, it depends on the problem to treat the maximal fitness
        # value as the best or to treat the minimal fitness value as the best.
        self.__fitnesses = numpy.zeros(self.__population, dtype=numpy.float32)
        self._elapsed_time = 0
        self._paused = False
        self._forceStop = False
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
        kernel_names = chromosome_wrapper.get_populate_kernel_names() +\
                        ["ocl_ga_calculate_fitness"] +\
                        chromosome_wrapper.get_crossover_kernel_names() +\
                        chromosome_wrapper.get_mutation_kernel_names();
        for name in kernel_names:
            utils.calculate_estimated_kernel_usage(prog,
                                                   ctx,
                                                   name)

    def __prepare_fitness_args(self):
        mf = cl.mem_flags
        self.__fitness_args_list = [self.__dev_chromosomes, self.__dev_fitnesses]

        self.__extra_fitness_args_list = []

        if self.__fitness_args is not None:
            ## create buffers for fitness arguments
            for arg in self.__fitness_args:
                cl_buffer = cl.Buffer(self.__ctx,
                                mf.READ_ONLY | mf.COPY_HOST_PTR,
                                hostbuf=numpy.array(arg["v"],
                                dtype=self.__type_to_numpy_type(arg["t"])))
                self.__extra_fitness_args_list.append(cl_buffer)
        # concatenate two fitness args list
        self.__fitness_args_list = self.__fitness_args_list + self.__extra_fitness_args_list

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
        self.__prepare_fitness_args()

        cl.enqueue_copy(self.__queue, self.__dev_fitnesses, self.__fitnesses)

        ## call preexecute_kernels for internal data structure preparation
        self.__sample_chromosome.preexecute_kernels(self.__ctx, self.__queue, self.__population)

        ## dump information on kernel resources usage
        self.__dump_kernel_info(self.__prg, self.__ctx, self.__sample_chromosome)

    def _populate_first_generations(self, prob_mutate, prob_crossover):
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
                                                  self.__dev_rnum,
                                                  self.__extra_fitness_args_list)

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

            if self._paused:
                self.__generation_index = i + 1
                self.__generation_time_diff = time.time() - start_time
                cl.enqueue_read_buffer(self.__queue, self.__dev_fitnesses, self.__fitnesses)
                cl.enqueue_read_buffer(self.__queue, self.__dev_chromosomes, self.__np_chromosomes).wait()
                break
            if self._forceStop:
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

            if self._paused:
                self.__generation_time_diff = time.time() - start_time
                cl.enqueue_read_buffer(self.__queue, self.__dev_fitnesses, self.__fitnesses)
                cl.enqueue_read_buffer(self.__queue, self.__dev_chromosomes, self.__np_chromosomes).wait()
                break
            if self._forceStop:
                cl.enqueue_read_buffer(self.__queue, self.__dev_fitnesses, self.__fitnesses)
                cl.enqueue_read_buffer(self.__queue, self.__dev_chromosomes, self.__np_chromosomes).wait()
                break

    def _start_evolution(self, prob_mutate, prob_crossover):
        generation_start = time.time()
        ## start the evolution
        if self.__termination["type"] == "time":
            self.__evolve_by_time(self.__termination["time"], prob_mutate, prob_crossover)
        elif self.__termination["type"] == "count":
            self.__evolve_by_count(self.__termination["count"], prob_mutate, prob_crossover)

        if self._paused:
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
        rnum = numpy.zeros(self.__population, dtype=numpy.uint32)
        cl.enqueue_read_buffer(self.__queue, self.__dev_rnum, rnum)
        cl.enqueue_read_buffer(self.__queue, self.__dev_fitnesses, self.__fitnesses)
        cl.enqueue_read_buffer(self.__queue, self.__dev_chromosomes, self.__np_chromosomes).wait()
        # save kernel memory to data
        data["rnum"] = rnum
        data["fitnesses"] = self.__fitnesses
        data["chromosomes"] = self.__np_chromosomes

        # save algorithm information
        data["prob_mutation"] = self.__prob_mutation
        data["prob_crossover"] = self.__prob_crossover

        self.__sample_chromosome.save(data, self.__ctx, self.__queue, self.__population)

    def __restore_state(self, data):
        # restore algorithm information
        self.__prob_mutation = data["prob_mutation"]
        self.__prob_crossover = data["prob_crossover"]

        self.__generation_index = data["generation_idx"]
        self.__dictStatistics = data["statistics"]
        self.__generation_time_diff = data["generation_time_diff"]
        self.__population = data["population"]

        rnum = data["rnum"]
        self.__fitnesses = data["fitnesses"]
        self.__np_chromosomes = data["chromosomes"]
        # build CL memory from restored memory
        mf = cl.mem_flags
        self.__dev_rnum = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                             hostbuf=numpy.array(rnum, dtype=numpy.uint32))
        self.__dev_chromosomes = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                    hostbuf=self.__np_chromosomes)
        self.__dev_fitnesses = cl.Buffer(self.__ctx, mf.WRITE_ONLY | mf.COPY_HOST_PTR,
                                         hostbuf=self.__fitnesses)
        self.__prepare_fitness_args()

        self.__sample_chromosome.restore(data, self.__ctx, self.__queue, self.__population)
        self._paused = True

    # public methods
    @EnterExit()
    def prepare(self):
        self.__preexecute_kernels()

    @EnterExit()
    def run(self, arg_prob_mutate = 0, arg_prob_crossover = 0):
        # This function is not supposed to be overriden
        prob_mutate = arg_prob_mutate if arg_prob_mutate else self.__prob_mutation
        prob_crossover = arg_prob_crossover if arg_prob_crossover else self.__prob_crossover
        assert 0 < prob_mutate < 1, "Make sure you've set it in options or passed when calling run."
        assert 0 < prob_crossover < 1, "Make sure you've set it in options or passed when calling run."
        assert self.thread != None

        self._forceStop = False
        task = GARun(self, prob_mutate, prob_crossover)
        self.thread.addtask(task)

    @EnterExit()
    def stop(self):
        self._forceStop = True
        if self.thread:
            self.thread.stop()
        self.thread = None

    @EnterExit()
    def pause(self):
        self._paused = True

    @EnterExit()
    def save(self, filename = None):
        assert self._paused, "save is only availabled while paused"
        data = dict()
        self.__save_state(data)
        fname = self.__saved_filename if self.__saved_filename else filename
        f = open(fname, "wb")
        pickle.dump(data, f)
        f.close()

    @EnterExit()
    def restore(self, filename = None):
        fname = self.__saved_filename if self.__saved_filename else filename
        # TODO : Should check file existence ?
        f = open(fname, "rb")
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
