#!/usr/bin/python3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from abc import ABCMeta
from utils import calc_linear_distance, plot_tsp_result, plot_grouping_result
import math
import random

class SAImpl(metaclass = ABCMeta):
    def __init__(self):
        self.temperature = 1000.0
        self.alpha = 0.9
        self.terminate_temperature = 0.00001
        self.iterations = 500
        pass

    ## Get the initial solution to anneal
    def get_init_solution(self):
        return None
    ## Calculate the cost of the solution
    def cost(self, solution):
        return None
    ## Return a new neighbor solution
    def neighbor(self, solution):
        return None
    ## Return a probability to decide whether accpet or not.
    def acceptance_probability(self, old_cost, new_cost, temperature):
        return None
    ## Start annealing
    def anneal(self):
        solution = self.get_init_solution()
        old_cost = self.cost(solution)
        # print('1st round : cost = {} '.format(old_cost))
        T = self.temperature
        T_min = self.terminate_temperature
        alpha = self.alpha
        while T > T_min:
            i = 1
            print('T={}'.format(T))
            while i <= self.iterations:
                new_solution = self.neighbor(solution)
                new_cost = self.cost(new_solution)
                ap = self.acceptance_probability(old_cost, new_cost, T)
                if ap > random.random():
                    solution = new_solution
                    old_cost = new_cost
                    # print('i={} round : cost = {} '.format(T, i, old_cost))
                i += 1
            T = T*alpha
        return solution

class ClassificationSolution(SAImpl):
    def __init__(self, group_info):
        SAImpl.__init__(self)
        self.group_info = group_info

    def get_init_solution(self):
        return self.group_info['init_solution']

    @staticmethod
    def get_init_params():
        # The number of points randomly generated
        num_points = 40
        random.seed()
        point_ids = list(range(0, num_points))
        point_info = {point_id: (random.random() * 100, random.random() * 100) for point_id in point_ids}
        pointX = [point_info[v][0] for v in point_info]
        pointY = [point_info[v][1] for v in point_info]

        # The number of group you want to divide.
        numOfGroups = 5
        group_id_set = list(range(0, numOfGroups))
        init_solution = [random.randint(0,numOfGroups-1) for x in range(num_points)]
        info = { 'num_of_group' : numOfGroups, 'init_solution' : init_solution,
                 'X' : pointX, 'Y' : pointY, 'g_set' : set(group_id_set),
                 'point_info' : point_info}
        return info

    ## For classification, we calculate the total distance among all points in
    ## the same group.
    def cost(self, solution):
        total = len(solution)
        cost = 0
        for i in range(self.group_info['num_of_group']):
            for j, gid in enumerate(solution):
                k = (j + 1)
                next_gid = gid
                while k < total:
                    next_gid = solution[k]
                    if gid == i and next_gid == i:
                        cost += calc_linear_distance(self.group_info['X'][j], self.group_info['Y'][j],
                                                     self.group_info['X'][k], self.group_info['Y'][k])
                    k += 1
        return cost

    ## Find a neighbor solution by swapping random two nodes.
    def neighbor(self, solution):
        neighbor = solution[:]
        total = len(solution)
        a = random.randint(0, total-1)
        b = random.randint(0, total-1)
        while a == b:
            b = random.randint(0, total-1)
        neighbor[a] = solution[b]
        neighbor[b] = solution[a]
        return neighbor

    def acceptance_probability(self, old_cost, new_cost, temperature):
        if new_cost < old_cost:
            return 1.0
        else:
            return math.exp(float(old_cost - new_cost) / temperature)

    def anneal(self):
        solution = SAImpl.anneal(self)
        plot_grouping_result(self.group_info['g_set'], solution, self.group_info['point_info'])
        return solution

class TSPSolution(SAImpl):
    def __init__(self, tsp_info):
        SAImpl.__init__(self)
        self.tsp_info = tsp_info

    def get_init_solution(self):
        return self.tsp_info['init_solution']

    @staticmethod
    def get_init_params():
        num_cities = 20
        random.seed()
        city_ids = list(range(0, num_cities))
        city_info = {city_id: (random.random() * 100, random.random() * 100) for city_id in city_ids}
        solution = list(city_info.keys())
        random.shuffle(solution)
        tsp_info = {}
        tsp_info['init_solution'] = solution
        tsp_info['city_info'] = city_info
        return tsp_info

    ## For TSP, we calculate the total distance between all cities.
    def cost(self, solution):
        city_info = self.tsp_info['city_info']
        total = len(city_info.keys())
        cost = 0
        for index, cid in enumerate(solution):
            first_city = cid
            next_city = solution[(index + 1) % total]

            cost += calc_linear_distance(city_info[first_city][0], city_info[first_city][1],
                                         city_info[next_city][0], city_info[next_city][1])
        return cost

    ## Find a neighbor solution by swapping random two nodes.
    def neighbor(self, solution):
        city_info = self.tsp_info['city_info']
        neighbor = solution[:]
        total = len(city_info.keys())
        a = random.randint(0, total-1)
        b = random.randint(0, total-1)
        while a == b:
            b = random.randint(0, total-1)
        neighbor[a] = solution[b]
        neighbor[b] = solution[a]
        return neighbor

    def acceptance_probability(self, old_cost, new_cost, temperature):
        if new_cost < old_cost:
            return 1.0
        else:
            return math.exp(float(old_cost - new_cost) / temperature)

    def anneal(self):
        solution = SAImpl.anneal(self)
        plot_tsp_result(self.tsp_info['city_info'], solution)
        return solution

class SimulatedAnnealing(object):
    def __init__(self, cls_solution):
        self.sas = cls_solution(cls_solution.get_init_params())
        pass

    ## To save the annealing state
    def save(self):
        pass

    ## To restore the annealing state
    def restore(self):
        pass

    ## Start annealing
    def anneal(self):
        best_solution = self.sas.anneal()
        return best_solution

def main():
    print('Input 1 for SA-TSP ; 2 for SA-Classification')
    try:
        sa = None
        int_choice = int(input())
        if int_choice == 1:
            sa = SimulatedAnnealing(TSPSolution)
        elif int_choice == 2:
            sa = SimulatedAnnealing(ClassificationSolution)
        else:
            print('Unsupported input, bye !')
            return None
        sa.anneal()
    except Exception as e:
        print('Exception : {}'.format(e))

if __name__ == '__main__':
    main()
