#!/usr/bin/python3
import os
import sys
import time
import random
import numpy
import pickle
import pyopencl as cl
import threading
from . import utils
from .utilities.generaltaskthread import TaskThread, Task, Logger

## A decorator class to notify state change before/after the action.
class EnterExit(object):
    def __call__(self, func):
        def wrapper(parent, *args, **kwargs):
            parent.state_machine.next(func.__name__)
            func(parent, *args, **kwargs)
            parent.state_machine.next('done')
        return wrapper

## A class which manages the state trasition.
#  @var openclga The OpenCLGA instance
#  @var __curr_state Current state.
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

    ## Transit to next state if (current state, action) is matched.
    #  After state changes, notify the change back to UI.
    #  @param action Could be the name of function or 'done'
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
        self.info('Change State : {} => {}'.format(last_state, next_state))
        if self.openclga.action_callbacks and 'state' in self.openclga.action_callbacks:
            self.openclga.action_callbacks['state'](next_state)

## A task to iterate GA generation in a separated thread.
class GARun(Task):
    def __init__(self, ga, prob_mutation, prob_crossover, callback):
        Task.__init__(self)
        self.ga = ga
        self.prob_m = prob_mutation
        self.prob_c = prob_crossover
        self.end_of_run = callback
        pass

    def run(self):
        start_time = time.time()
        # No need to generate new population for pause or restore.
        self.ga._generate_population_if_needed(self.prob_m, self.prob_c)
        self.ga._start_evolution(self.prob_m, self.prob_c)

        self.ga._elapsed_time += time.time() - start_time
        self.end_of_run()

## Implementation of the flow of GA on OpenCL.
#  Initialize opencl command queue, collect include path, build programs.
#  @param options Used to initizlize all member variables
#  @param action_callbacks Called when state is changed and carry execution status
#                          back to ocl_ga_worker.
class OpenCLGA():
    def __init__(self, options, action_callbacks = {}):
        if action_callbacks is not None:
            for action, cb in action_callbacks.items():
                assert callable(cb)
        self.state_machine = StateMachine(self, 'waiting')
        self.__init_members(options)
        extra_path = options.get('extra_include_path', [])
        cl_context = options.get('cl_context', None)
        self.__init_cl(cl_context, extra_path)
        self.__create_program()
        self.action_callbacks = action_callbacks

    ## public properties
    @property
    def paused(self):
        return self._paused

    @property
    def elapsed_time(self):
        return self._elapsed_time

    ## private properties
    @property
    def __early_terminated(self):
        return self.__sample_chromosome.early_terminated(self.__best_fitnesses[0],
                                                         self.__worst_fitnesses[0])

    @property
    def __args_codes(self):
        opt_for_max = 0 if self.__opt_for_max == 'min' else 1
        return '#define OPTIMIZATION_FOR_MAX ' + str(opt_for_max) + '\n'

    @property
    def __populate_codes(self):
        return '#define POPULATION_SIZE ' + str(self.__population) + '\n' +\
               '#define CHROMOSOME_TYPE ' +  self.__sample_chromosome.struct_name + '\n'

    @property
    def __evaluate_code(self):
        chromosome = self.__sample_chromosome
        if self.__fitness_args is not None:
            fit_args = ', '.join(['global ' + v['t'] + '* _f_' + v['n'] for v in self.__fitness_args])
            fit_argv = ', '.join(['_f_' + v['n'] for v in self.__fitness_args])
            if len(fit_args) > 0:
                fit_args = ', ' + fit_args
                fit_argv = ', ' + fit_argv
        else:
            fit_args = ''
            fit_argv = ''

        return '#define CHROMOSOME_SIZE ' + chromosome.chromosome_size_define + '\n' +\
               '#define CALCULATE_FITNESS ' + self.__fitness_function + '\n' +\
               '#define FITNESS_ARGS ' + fit_args + '\n'+\
               '#define FITNESS_ARGV ' + fit_argv + '\n'

    @property
    def __include_code(self):
        sample_gene = self.__sample_chromosome.genes[0]
        return self.__sample_chromosome.kernelize() + '\n' +\
               '#include "' + sample_gene.kernel_file + '"\n' +\
               '#include "' + self.__sample_chromosome.kernel_file + '"\n\n'

    ## private methods
    #  @var __dictStatistics A dictionary. e.g. { gen : { 'best':  best_fitness,
    #                                                     'worst': worst_fitness,
    #                                                     'avg':   avg_fitness },
    #                                            'avg_time_per_gen': avg. elapsed time per generation }
    #  @var thread The thread runs the actual algorithm.
    #  @var __population The number of population
    #  @var __termination A dictionary to identify the termination condition.
    #                     If type is 'time', it means that the iteration will be
    #                     ended after it runs the amount of time.
    #                     If type is 'count', it means that the iteration will be
    #                     ended when it runs the amount of iterations.
    #  @var __opt_for_max Larger fitness means better solution if 'max', smaller
    #                     fitness is better if it's set to 'min'.
    #  @var __np_chromosomes The numpy memory which stores the dna of genes of all
    #                        chromosomes.
    #  @var __is_elitism_mode Off = 0, On = 1. If On, spare chromosomes memory will
    #                      be prepared to hold the best chromosomes of all clients.
    #                      Then put these best of bests into next-gen population.
    # @var __elitism_top The number of elites to be picked in each generation.
    # @var __elitism_every The number of rounds for server to notify all clients
    #                      that newly sorted elites are coming
    # @var __elites_updated Indicating that newly sorted elites are received.
    #                       These elites are going to be updated into dev memory.
    # @var __best_fitnesses The list of top N best fitnesses
    # @var __worst_fitnesses The list of bottom N worst fitnesses
    # @var __best_indices The list of indices of top N best fitnesses
    # @var __worst_indices The list of indices of bottom N worst fitnesses
    # @var __avg The average of all fitnesses
    # @var __extinction A dictionary to identify if a extinction is needed.
    #                   If type is 'best_worst', an exticntion will be triggered
    #                   when the difference between best fitness and worst fitness is
    #                   smaller than expected value.
    #                   If type is 'best_avg', the operation will be triggered
    #                   when the difference between best fitness and avg fitness
    #                   is smaller than expected value.
    # @var _pausing_evt Wait when entering pausing state, it will be set right after
    #                   that particular iteration ends.
    def __init_members(self, options):
        self.thread = TaskThread(name='GARun')
        self.thread.daemon = True
        self.thread.start()

        self.__sample_chromosome = options['sample_chromosome']
        self.__termination = options['termination']
        self.__population = options['population']
        self.__opt_for_max = options.get('opt_for_max', 'max')
        self.__np_chromosomes = None
        self.__fitness_function = options['fitness_func']
        self.__fitness_kernel_str = options['fitness_kernel_str']
        self.__fitness_args = options.get('fitness_args', None)

        # For elitism_mode
        elitism_info = options.get('elitism_mode', {})
        self.__elitism_top = elitism_info.get('top', 0)
        self.__elitism_every = elitism_info.get('every', 0)
        self.__is_elitism_mode = all([self.__elitism_top, self.__elitism_every])
        self.__elites_updated = False
        self.__elite_lock = threading.Lock()

        # List of fitness and index.
        size_of_indices = self.__elitism_top if self.__is_elitism_mode else 1
        self.__best_fitnesses = numpy.zeros(size_of_indices, dtype=numpy.float32)
        self.__worst_fitnesses = numpy.zeros(size_of_indices, dtype=numpy.float32)
        self.__best_indices = numpy.zeros(size_of_indices, dtype=numpy.int32)
        self.__worst_indices = numpy.zeros(size_of_indices, dtype=numpy.int32)
        self.__avg = 0

        self.__saved_filename = options.get('saved_filename', None)
        self.__prob_mutation = options.get('prob_mutation', 0)
        self.__prob_crossover = options.get('prob_crossover', 0)
        self.__dictStatistics = {}

        # Generally in GA, it depends on the problem to treat the maximal fitness
        # value as the best or to treat the minimal fitness value as the best.
        self.__fitnesses = numpy.zeros(self.__population, dtype=numpy.float32)
        self._elapsed_time = 0
        self._populated = False
        self._pausing_evt = threading.Event()
        self._paused = False
        self._forceStop = False
        self.__generation_index = 0
        self.__generation_time_diff = 0
        self.__debug_mode = 'debug' in options
        self.__generation_callback = options['generation_callback']\
                                        if 'generation_callback' in options else None

        self.__extinction = options['extinction']\
                                if 'extinction' in options else None

    def __init_cl(self, cl_context, extra_include_path):
        # create OpenCL context, queue, and memory
        # NOTE: Please set PYOPENCL_CTX=N (N is the device number you want to use)
        #       at first if it's in external_process mode, otherwise a exception
        #       will be thrown, since it's not in interactive mode.
        # TODO: Select a reliable device during runtime by default.
        self.__ctx = cl_context if cl_context is not None else cl.create_some_context()
        self.__queue = cl.CommandQueue(self.__ctx)
        self.__include_path = []
        kernel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kernel')
        paths = extra_include_path + [kernel_path]
        for path in paths:
            escapedPath = path.replace(' ', '^ ') if sys.platform.startswith('win')\
                                                  else path.replace(' ', '\\ ')
            # After looking into the source code of pyopencl/__init__.py
            # '-I' and folder path should be sepearetd. And ' should not included in string path.
            self.__include_path.append('-I')
            self.__include_path.append(os.path.join(os.getcwd(), escapedPath))

    def __create_program(self):
        codes = self.__args_codes + '\n' +\
                self.__populate_codes + '\n' +\
                self.__evaluate_code + '\n' +\
                self.__include_code + '\n' +\
                self.__fitness_kernel_str
        kernel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kernel')
        f = open(os.path.join(kernel_path, 'ocl_ga.cl'), 'r')
        fstr = ''.join(f.readlines())
        f.close()
        if self.__debug_mode:
            fdbg = open('final.cl', 'w')
            fdbg.write(codes + fstr)
            fdbg.close()

        self.__prg = cl.Program(self.__ctx, codes + fstr).build(self.__include_path);

    def __type_to_numpy_type(self, t):
        if t == 'float':
            return numpy.float32
        elif t == 'int':
            return numpy.int32
        else:
            raise 'unsupported python type'

    def __dump_kernel_info(self, prog, ctx, chromosome_wrapper, device = None):
        kernel_names = chromosome_wrapper.get_populate_kernel_names() +\
                        ['ocl_ga_calculate_fitness'] +\
                        chromosome_wrapper.get_crossover_kernel_names() +\
                        chromosome_wrapper.get_mutation_kernel_names();
        for name in kernel_names:
            utils.calculate_estimated_kernel_usage(prog,
                                                   ctx,
                                                   name)

    def __is_extinction_matched(self, best, avg, worst):
        if self.__extinction is None:
            return False

        assert('type' in self.__extinction)
        assert('diff' in self.__extinction)

        if self.__extinction['type'] == 'best_worst':
            return abs(best - worst) < self.__extinction['diff']
        elif self.__extinction['type'] == 'best_avg':
            return abs(best - avg) < self.__extinction['diff']

        return False

    def __prepare_fitness_args(self):
        mf = cl.mem_flags
        self.__fitness_args_list = [self.__dev_chromosomes, self.__dev_fitnesses]

        self.__extra_fitness_args_list = []

        if self.__fitness_args is not None:
            ## create buffers for fitness arguments
            for arg in self.__fitness_args:
                cl_buffer = cl.Buffer(self.__ctx,
                                mf.READ_ONLY | mf.COPY_HOST_PTR,
                                hostbuf=numpy.array(arg['v'],
                                dtype=self.__type_to_numpy_type(arg['t'])))
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

        if self.__is_elitism_mode:
            self.__elites_updated = False
            self.__current_elites = numpy.zeros(self.__sample_chromosome.dna_total_length * self.__elitism_top,
                                                dtype=numpy.int32)
            self.__dev_current_elites = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                                  hostbuf=self.__current_elites)
            self.__updated_elites = numpy.zeros(self.__sample_chromosome.dna_total_length * self.__elitism_top,
                                                dtype=numpy.int32)
            self.__dev_updated_elites = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                                  hostbuf=self.__updated_elites)
            self.__updated_elite_fitnesses = numpy.zeros(self.__elitism_top,
                                                        dtype=numpy.float32)
            self.__dev_updated_elite_fitnesses = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                                           hostbuf=self.__updated_elite_fitnesses)

        # For statistics
        self.__dev_best_indices = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                            hostbuf=self.__best_indices)
        self.__dev_worst_indices = cl.Buffer(self.__ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                             hostbuf=self.__worst_indices)

        cl.enqueue_copy(self.__queue, self.__dev_fitnesses, self.__fitnesses)

        ## call preexecute_kernels for internal data structure preparation
        self.__sample_chromosome.preexecute_kernels(self.__ctx, self.__queue, self.__population)

        ## dump information on kernel resources usage
        self.__dump_kernel_info(self.__prg, self.__ctx, self.__sample_chromosome)

    ## Populate the first generation.
    def _generate_population_if_needed(self, prob_mutate, prob_crossover):
        if self._populated:
            return
        self._populated = True
        self.__sample_chromosome.execute_populate(self.__prg,
                                                  self.__queue,
                                                  self.__population,
                                                  self.__dev_chromosomes,
                                                  self.__dev_rnum)

        self.__prg.ocl_ga_calculate_fitness(self.__queue,
                                            (self.__population,),
                                            (1,),
                                            *self.__fitness_args_list).wait()

    def __examine_single_generation(self, index):
        # we cannot extinct the first generation
        if index == 0:
            return

        last_result = self.__dictStatistics[index - 1]

        should_extinct = self.__is_extinction_matched(last_result['best'],
                                                      last_result['avg'],
                                                      last_result['worst'])

        if should_extinct == False:
            return

        assert('ratio' in self.__extinction)
        # To add 1 for preventing 0 if the population size is too small.
        size = int(self.__population * self.__extinction['ratio']) + 1
        self.__sample_chromosome.execute_populate(self.__prg,
                                                  self.__queue,
                                                  size,
                                                  self.__dev_chromosomes,
                                                  self.__dev_rnum)

    def __execute_single_generation(self, index, prob_mutate, prob_crossover):
        self.__examine_single_generation(index)

        best_fitness = self.__best_fitnesses[0]

        if self.__is_elitism_mode and self.__elites_updated:
            with self.__elite_lock:
                best_fitness = self.__updated_elite_fitnesses[0]
                # Update current N elites to device memory.
                self.__sample_chromosome.execute_update_current_elites(self.__prg,
                                                                    self.__queue,
                                                                    self.__elitism_top,
                                                                    self.__dev_worst_indices,
                                                                    self.__dev_chromosomes,
                                                                    self.__dev_updated_elites,
                                                                    self.__dev_fitnesses,
                                                                    self.__dev_updated_elite_fitnesses)
                self.__elites_updated = False

        self.__sample_chromosome.selection_preparation(self.__prg,
                                                       self.__queue,
                                                       self.__dev_fitnesses)


        # We want to prevent the best one being changed.
        if abs(self.__best_fitnesses[0] - self.__worst_fitnesses[0]) >= 0.00001:
            self.__sample_chromosome.execute_crossover(self.__prg,
                                                       self.__queue,
                                                       self.__population,
                                                       index,
                                                       prob_crossover,
                                                       self.__dev_chromosomes,
                                                       self.__dev_fitnesses,
                                                       self.__dev_rnum,
                                                       best_fitness)

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

        # We calculate best / worst / avg fitness in system memory for
        # better efficiency & code simplicity.
        cl.enqueue_copy(self.__queue, self.__fitnesses, self.__dev_fitnesses)

        self.__update_fitness_index_pair()

        if self.__is_elitism_mode:
            # Find current N elites and their corresponding indices, then read
            # it back from device memory to system memory.
            self.__sample_chromosome.execute_get_current_elites(self.__prg,
                                                                self.__queue,
                                                                self.__elitism_top,
                                                                self.__dev_chromosomes,
                                                                self.__dev_current_elites,
                                                                self.__dev_best_indices)
            cl.enqueue_copy(self.__queue, self.__current_elites, self.__dev_current_elites)

        self.__dictStatistics[index] = {}
        self.__dictStatistics[index]['best'] = self.__best_fitnesses[0]
        self.__dictStatistics[index]['worst'] = self.__worst_fitnesses[0]
        self.__dictStatistics[index]['avg'] = self.__avg
        if self.__generation_callback is not None:
            self.__generation_callback(index, self.__dictStatistics[index])

    ## This is called at the end of each generation.
    #  It helps to update current top N & bottom N fitnesses and indices of
    #  all chromosomes and then calculate the avg fitness.
    def __update_fitness_index_pair(self):
        ori = []
        fitness_sum = 0.0
        for idx, fitness in enumerate(self.__fitnesses):
            ori.append((idx, fitness))
            fitness_sum += fitness
        self.__avg = fitness_sum / len(self.__fitnesses)

        assert len(self.__best_indices) == len(self.__best_fitnesses)
        assert len(self.__worst_indices) == len(self.__worst_fitnesses)
        size_of_indices = len(self.__best_indices)

        ori.sort(key=lambda item : item[1], reverse=self.__opt_for_max=='max')
        tops = ori[:size_of_indices]
        bottoms = ori[len(ori)-size_of_indices:]
        for idx in range(size_of_indices):
            self.__best_indices[idx] = tops[idx][0]
            self.__best_fitnesses[idx] = tops[idx][1]
            self.__worst_indices[idx] = bottoms[idx][0]
            self.__worst_fitnesses[idx] = bottoms[idx][1]

        with self.__elite_lock:
            cl.enqueue_copy(self.__queue, self.__dev_best_indices, self.__best_indices)
            cl.enqueue_copy(self.__queue, self.__dev_worst_indices, self.__worst_indices)

    def __evolve_by_count(self, count, prob_mutate, prob_crossover):
        start_time = time.time()
        for i in range(self.__generation_index, count):
            self.__execute_single_generation(i, prob_mutate, prob_crossover)
            if self.__early_terminated:
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
            if self.__early_terminated or elapsed_time > max_time:
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
        if self.__termination['type'] == 'time':
            self.__evolve_by_time(self.__termination['time'], prob_mutate, prob_crossover)
        elif self.__termination['type'] == 'count':
            self.__evolve_by_count(self.__termination['count'], prob_mutate, prob_crossover)

        if self._paused:
            return

        cl.enqueue_read_buffer(self.__queue, self.__dev_fitnesses, self.__fitnesses)
        cl.enqueue_read_buffer(self.__queue, self.__dev_chromosomes, self.__np_chromosomes).wait()

        total_time_consumption = time.time() - generation_start + self.__generation_time_diff
        avg_time_per_gen = total_time_consumption / float(len(self.__dictStatistics))
        self.__dictStatistics['avg_time_per_gen'] = avg_time_per_gen

    def __save_state(self, data):
        # save data from intenal struct
        data['generation_idx'] = self.__generation_index
        data['statistics'] = self.__dictStatistics
        data['generation_time_diff'] = self.__generation_time_diff
        data['population'] = self.__population

        # read data from kernel
        rnum = numpy.zeros(self.__population, dtype=numpy.uint32)
        cl.enqueue_copy(self.__queue, rnum, self.__dev_rnum)
        cl.enqueue_copy(self.__queue, self.__fitnesses, self.__dev_fitnesses)
        cl.enqueue_copy(self.__queue, self.__np_chromosomes, self.__dev_chromosomes)

        # save kernel memory to data
        data['rnum'] = rnum
        data['fitnesses'] = self.__fitnesses
        data['chromosomes'] = self.__np_chromosomes
        data['best'] = self.__best_fitnesses[0]
        data['worst'] = self.__worst_fitnesses[0]
        data['avg'] = self.__avg

        # save algorithm information
        data['prob_mutation'] = self.__prob_mutation
        data['prob_crossover'] = self.__prob_crossover

        self.__sample_chromosome.save(data, self.__ctx, self.__queue, self.__population)

    def __restore_state(self, data):
        # restore algorithm information
        self.__prob_mutation = data['prob_mutation']
        self.__prob_crossover = data['prob_crossover']

        self.__generation_index = data['generation_idx']
        self.__dictStatistics = data['statistics']
        self.__generation_time_diff = data['generation_time_diff']
        self.__population = data['population']

        rnum = data['rnum']
        self.__fitnesses = data['fitnesses']
        self.__np_chromosomes = data['chromosomes']
        self.__best_fitnesses = data['best']
        self.__worst_fitnesses = data['worst']
        self.__avg = data['avg']

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

    def __end_of_run(self):
        if self._paused:
            self._pausing_evt.set()
        else:
            t = threading.Thread(target=self.stop)
            t.daemon = True
            t.start()

    @EnterExit()
    def run(self, arg_prob_mutate = 0, arg_prob_crossover = 0):
        # This function is not supposed to be overriden
        prob_mutate = arg_prob_mutate if arg_prob_mutate else self.__prob_mutation
        prob_crossover = arg_prob_crossover if arg_prob_crossover else self.__prob_crossover
        assert 0 < prob_mutate < 1, 'Make sure you have set it in options or passed when calling run.'
        assert 0 < prob_crossover < 1, 'Make sure you have set it in options or passed when calling run.'
        assert self.thread != None

        self._forceStop = False
        self._paused = False
        task = GARun(self, prob_mutate, prob_crossover, self.__end_of_run)
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
        self._pausing_evt.wait()
        self._pausing_evt.clear()

    @EnterExit()
    def save(self, filename = None):
        assert self._paused, 'save is only availabled while paused'
        data = dict()
        self.__save_state(data)
        fname = self.__saved_filename if self.__saved_filename else filename
        f = open(fname, 'wb')
        pickle.dump(data, f)
        f.close()

    @EnterExit()
    def restore(self, filename = None):
        fname = self.__saved_filename if self.__saved_filename else filename
        # TODO : Should check file existence ?
        f = open(fname, 'rb')
        data = pickle.load(f)
        f.close()
        self.__restore_state(data)

    def get_statistics(self):
        return self.__dictStatistics

    ## Return a dictionary containers current elites and their fitnesses
    #  correspondingly. e.g.
    #  elites : abcdedabcdefdeeacbadeadebcda
    #  fitnesses : 4, 5.5, 3.7, 7.1
    #  dna_size : 7
    #  The total lenght of elites is 28. With dna_size being 7, you could
    #  divided elites into 4 seperate array. Each standands for a chromosome
    #  with corresponding fitnesses orderly.
    def get_current_elites_info(self):
        elites_info = {}
        if self.__is_elitism_mode:
            elites_info = { 'elites' : self.__current_elites,
                            'fitnesses' : self.__best_fitnesses,
                            'dna_size' : self.__sample_chromosome.dna_total_length }
        return elites_info

    def get_the_best(self):
        assert self.__opt_for_max in ['max', 'min']

        best_fitness = eval(self.__opt_for_max)(value for value in self.__fitnesses)
        best_index = list(self.__fitnesses).index(best_fitness)

        # We had convert chromosome to a cyclic gene. So, the num_of_genes in CL is more than python
        # by one.
        startGeneId = best_index * (self.__sample_chromosome.num_of_genes)
        endGeneId = (best_index + 1) * (self.__sample_chromosome.num_of_genes)
        best = [v for v in self.__np_chromosomes[startGeneId:endGeneId]]
        return best, best_fitness, self.__sample_chromosome.from_kernel_value(best)

    ## Update the top N(sorted) elites of all elites provided from all workers
    #  to chromosomes device memory.
    def update_elites(self, elites):
        assert self.__is_elitism_mode, 'Elitism Mode is {}'.format(self.__is_elitism_mode)
        assert len(elites) == self.__elitism_top
        elites_dna_data = []
        elites_fitnesses = []
        # Concatenate all elites' dna / fitness into a single continuous memory
        # layout.
        for idx, elite_info in enumerate(elites):
            fitness, elite_dna, worker_id = elite_info
            if idx == 0:
                print('updating {}/{} elites ... fitness = {} from worker {}'.format(idx+1, len(elites), fitness, worker_id))
            elites_dna_data.extend(elite_dna)
            elites_fitnesses.append(fitness)

        # Convert the continuous memory to a device compatible memory layout.
        self.__updated_elites = numpy.asarray(elites_dna_data, dtype=numpy.int32)
        self.__updated_elite_fitnesses = numpy.asarray(elites_fitnesses, dtype=numpy.float32)

        # Transfer it into device meory.
        with self.__elite_lock:
            cl.enqueue_copy(self.__queue, self.__dev_updated_elites, self.__updated_elites)
            cl.enqueue_copy(self.__queue, self.__dev_updated_elite_fitnesses, self.__updated_elite_fitnesses)

        self.__elites_updated = True
