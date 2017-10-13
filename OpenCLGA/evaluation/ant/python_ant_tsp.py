#!/usr/bin/python3
import math
import numpy
import random
import sys
from OpenCLGA import utils

class PythonAntTSP():

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

        self.__init_member()

    def __init_member(self):
        self.__calculate_distances()
        # initialize all pheromones of paths with 1
        self.__path_pheromones = numpy.empty(shape=[self.__node_count, self.__node_count],
                                             dtype=numpy.float32)
        self.__path_pheromones.fill(1)
        self.__best_result = None
        self.__best_fitness = sys.float_info.max

    def __calculate_distances(self):
        # calculate the distances betwen two points.
        self.__path_distances = numpy.empty(shape=[self.__node_count, self.__node_count],
                                            dtype=numpy.float32)
        for start in range(self.__node_count):
            for end in range(self.__node_count):
                if start == end:
                    self.__path_distances[(start, end)] = 0
                else:
                    self.__path_distances[(start, end)] = math.hypot(self.__nodes[start][0] - self.__nodes[end][0],
                                                                     self.__nodes[start][1] - self.__nodes[end][1])

    def __calculate_path_probabilities(self, visited_nodes):
        path_probabilities = numpy.empty(shape=[self.__node_count], dtype=numpy.float32)
        pheromones = numpy.empty(shape=[self.__node_count], dtype=numpy.float32)
        total = 0.0
        current_node = visited_nodes[-1]
        for end in range(self.__node_count):
            if current_node == end:
                pheromones[end] = 0
            elif end in visited_nodes:
                pheromones[end] = 0
            else:
                pheromones[end] = (self.__path_pheromones[(current_node, end)] ** self.__alpha) * ((1 / self.__path_distances[(current_node, end)]) ** self.__beta)
                total += pheromones[end]

        for end in range(self.__node_count):
            if current_node == end:
                path_probabilities[end] = 0
            elif end in visited_nodes:
                path_probabilities[end] = 0
            else:
                path_probabilities[end] = pheromones[end] / total

        return path_probabilities

    def __random_choose(self, probabilities):
        rnd = random.random()
        for end in range(self.__node_count):
            if probabilities[end] == 0:
                continue
            elif rnd >= probabilities[end]:
                rnd -= probabilities[end]
            else:
                return end


    def __update_path_pheromones(self, visited_nodes, fitness):
        for index, node in enumerate(visited_nodes):
            if index < len(visited_nodes) - 1:
                if node < visited_nodes[index + 1]:
                    self.__path_pheromones[(node, visited_nodes[index + 1])] += self.__q / fitness;
                else:
                    self.__path_pheromones[(visited_nodes[index + 1], node)] += self.__q / fitness;
            else:
                if node < visited_nodes[0]:
                    self.__path_pheromones[(node, visited_nodes[0])] += self.__q / fitness;
                else:
                    self.__path_pheromones[(visited_nodes[0], node)] += self.__q / fitness;

    def __calculate_visited_fitness(self, visited_nodes):
        result = 0.0;
        for index, node in enumerate(visited_nodes):
            if index < len(visited_nodes) - 1:
                if node < visited_nodes[index + 1]:
                    result += self.__path_distances[(node, visited_nodes[index + 1])]
                else:
                    result += self.__path_distances[(visited_nodes[index + 1], node)]
            else:
                if node < visited_nodes[0]:
                    result += self.__path_distances[(node, visited_nodes[0])]
                else:
                    result += self.__path_distances[(visited_nodes[0], node)]
        return result

    def __execute_single_generation(self, generation):
        ant_result = []
        # send a lot of ants out
        for ant in range(self.__ants):
            visited_nodes = [random.randint(0, self.__node_count - 1)]
            # run all nodes
            while len(visited_nodes) < self.__node_count:
                probabilities = self.__calculate_path_probabilities(visited_nodes)
                visited_nodes.append(self.__random_choose(probabilities))

            # calculate fitness
            fitness = self.__calculate_visited_fitness(visited_nodes)
            ant_result.append((visited_nodes, fitness))
            # update best
            if fitness < self.__best_fitness:
                self.__best_fitness = fitness
                self.__best_result = visited_nodes

        # evaporate the pheromones on each path and increase a base value.
        for start, value1 in enumerate(self.__path_pheromones):
            for end, value2 in enumerate(value1):
                self.__path_pheromones[(start, end)] *= (1 - self.__evaporation)
                self.__path_pheromones[(start, end)] += 1

        # update pheromone
        for result in ant_result:
            self.__update_path_pheromones(result[0], result[1])

    def run(self):
        for generation in range(self.__iterations):
            self.__execute_single_generation(generation)
            print('best fitness #{}: {}'.format(generation, self.__best_fitness))

        return (self.__best_result, self.__best_fitness)

if __name__ == '__main__':
    random.seed(1)
    city_info = { city_id: (random.random() * 100, random.random() * 100) for city_id in range(30) }
    print('cities:')
    print(city_info)
    ant = PythonAntTSP({
        'iterations': 20,
        'ants': 100,
        'alpha': 1,
        'beta': 9,
        'evaporation': 0.9,
        'q': 10000,
        'nodes': city_info
    })

    result = ant.run()
    print('Length: {}'.format(result[1]))
    print('Shortest Path: ' + ' => '.join(str(g) for g in result[0]))
    utils.plot_tsp_result(city_info, result[0])
