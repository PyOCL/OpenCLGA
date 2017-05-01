#!/usr/bin/python3
import os
import random
from OpenCLGA import SimpleGene, SimpleChromosome, utils, OpenCLGA

def show_generation_info(index, data_dict):
    print('{0}\t\t==> {1}'.format(index, data_dict['best']))

def run(num_chromosomes, generations):
    random.seed(123)

    type1 = ['q12', 'q23', 'q34']
    type2 = ['q1', 'q2', 'q3', 'q4']

    sample = SimpleChromosome([SimpleGene('q12', type1, 'unit-1'),
                               SimpleGene('q12', type1, 'unit-2'),
                               SimpleGene('q1', type2, 'unit-3'),
                               SimpleGene('q1', type2, 'unit-4'),
                               SimpleGene('q1', type2, 'unit-5'),
                               SimpleGene('q1', type2, 'unit-6'),
                               SimpleGene('q1', type2, 'unit-7')])

    self_path = os.path.dirname(os.path.abspath(__file__))
    ocl_kernels = os.path.realpath(os.path.join(self_path, '..', '..', 'OpenCLGA', 'kernel'))
    f = open(os.path.join(self_path, 'power.cl'), 'r')
    fstr = ''.join(f.readlines())
    f.close()

    import threading
    evt = threading.Event()
    evt.clear()
    def state_changed(state):
        if 'stopped' == state:
            evt.set()

    ga_cl = OpenCLGA({'sample_chromosome': sample,
                          'termination': {
                            'type': 'count',
                            'count': generations
                          },
                          'population': num_chromosomes,
                          'fitness_kernel_str': fstr,
                          'fitness_func': 'power_station_fitness',
                          'extra_include_path': [ocl_kernels],
                          'opt_for_max': 'max',
                          'debug': True,
                          'generation_callback': show_generation_info},
                          action_callbacks = {'state' : state_changed})

    ga_cl.prepare()

    prob_mutate = 0.1
    prob_cross = 0.8
    ga_cl.run(prob_mutate, prob_cross)
    evt.wait()

    utils.plot_ga_result(ga_cl.get_statistics())
    print('run took', ga_cl.elapsed_time, 'seconds')
    best_chromosome, best_fitness, best_info = ga_cl.get_the_best()
    print('Best Fitness: %f'%(best_fitness))
    print('1 ~ 7 units are maintained at: ' + ', '.join(str(g.dna) for g in best_info.genes))

if __name__ == '__main__':
    run(num_chromosomes=100, generations=100)
