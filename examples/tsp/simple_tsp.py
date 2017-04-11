#!/usr/bin/python3
import os
import random
from OpenCLGA import SimpleGene, ShufflerChromosome, utils, OpenCLGA

def show_generation_info(index, data_dict):
    print('{0}\t\t==> {1}'.format(index, data_dict['best']))

def run(num_chromosomes, generations):
    num_cities = 20
    random.seed(119)
    city_ids = list(range(0, num_cities))
    city_info = {city_id: (random.random() * 100, random.random() * 100) for city_id in city_ids}

    sample = ShufflerChromosome([SimpleGene(v, city_ids) for v in city_ids])

    tsp_path = os.path.dirname(os.path.abspath(__file__))
    ocl_kernels = os.path.realpath(os.path.join(tsp_path, '..', '..', 'kernel'))
    tsp_kernels = os.path.join(tsp_path, 'kernel')

    f = open(os.path.join(tsp_kernels, 'simple_tsp.cl'), 'r')
    fstr = ''.join(f.readlines())
    f.close()

    pointX = [str(city_info[v][0]) for v in city_info];
    pointY = [str(city_info[v][1]) for v in city_info]

    import threading
    evt = threading.Event()
    evt.clear()
    def state_changed(state):
        if 'stopped' == state:
            evt.set()

    tsp_ga_cl = OpenCLGA({'sample_chromosome': sample,
                          'termination': {
                            'type': 'count',
                            'count': generations
                          },
                          'population': num_chromosomes,
                          'fitness_kernel_str': fstr,
                          'fitness_func': 'simple_tsp_fitness',
                          'fitness_args': [{'t': 'float', 'v': pointX, 'n': 'x'},
                                           {'t': 'float', 'v': pointY, 'n': 'y'}],
                          'extra_include_path': [ocl_kernels],
                          'opt_for_max': 'min',
                          'debug': True,
                          'generation_callback': show_generation_info},
                          action_callbacks = {'state' : state_changed})

    tsp_ga_cl.prepare()

    prob_mutate = 0.1
    prob_cross = 0.8
    tsp_ga_cl.run(prob_mutate, prob_cross)
    evt.wait()

    utils.plot_ga_result(tsp_ga_cl.get_statistics())
    print('run took', tsp_ga_cl.elapsed_time, 'seconds')
    best_chromosome, best_fitness, best_info = tsp_ga_cl.get_the_best()
    print('Best Fitness: %f'%(best_fitness))
    print('Shortest Path: ' + ' => '.join(str(g) for g in best_chromosome))
    utils.plot_tsp_result(city_info, best_chromosome)

if __name__ == '__main__':
    run(num_chromosomes=4000, generations=1000)
