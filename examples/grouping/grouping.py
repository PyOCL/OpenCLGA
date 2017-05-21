#!/usr/bin/python3
import os
import random
from OpenCLGA import SimpleGene, SimpleChromosome, ShufflerChromosome, utils, OpenCLGA

def show_generation_info(index, data_dict):
    print('{0}\t\t==> {1}'.format(index, data_dict['best']))

def run(num_chromosomes, generations):
    random.seed()

    # The number of points randomly generated
    num_points = 100
    random.seed()
    point_ids = list(range(0, num_points))
    point_info = {point_id: (random.random() * 100, random.random() * 100) for point_id in point_ids}
    pointX = [str(point_info[v][0]) for v in point_info];
    pointY = [str(point_info[v][1]) for v in point_info]

    # The number of group you want to divide.
    numOfGroups = 10
    group_id_set = list(range(0, numOfGroups))
    group_ids = [random.randint(0,numOfGroups-1) for x in range(num_points)]

    sample = SimpleChromosome([SimpleGene(groupd_id, group_id_set) for groupd_id in group_ids])

    self_path = os.path.dirname(os.path.abspath(__file__))
    f = open(os.path.join(self_path, 'grouping.cl'), 'r')
    fstr = ''.join(f.readlines())
    f.close()

    import threading
    evt = threading.Event()
    evt.clear()
    def state_changed(state):
        if 'stopped' == state:
            evt.set()

    ga_cl = OpenCLGA({'sample_chromosome': sample,
                      'termination': { 'type': 'count',
                                       'count': generations },
                      'population': num_chromosomes,
                      'fitness_kernel_str': fstr,
                      'fitness_func': 'grouping_fitness',
                      'fitness_args': [{'t': 'int', 'v': numOfGroups, 'n': 'numOfGroups'},
                                       {'t': 'float', 'v': pointX, 'n': 'x'},
                                       {'t': 'float', 'v': pointY, 'n': 'y'}],
                      'opt_for_max': 'min',
                      'debug': True,
                      'generation_callback': show_generation_info},
                      action_callbacks = {'state' : state_changed})

    ga_cl.prepare()

    prob_mutate = 0.1
    prob_cross = 0.8
    ga_cl.run(prob_mutate, prob_cross)
    evt.wait()

    print('run took', ga_cl.elapsed_time, 'seconds')
    best_chromosome, best_fitness, best_info = ga_cl.get_the_best()
    print(best_chromosome)
    utils.plot_grouping_result(group_id_set, best_chromosome, point_info)

if __name__ == '__main__':
    run(num_chromosomes=2000, generations=2000)
