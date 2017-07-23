#!/usr/bin/python3
from abc import ABCMeta
from utils import calc_linear_distance, plot_tsp_result
import math
import random

class SAImpl(metaclass = ABCMeta):
    def __init__(self):
        pass
    ## Calculate the cost of the solution
    def cost(self, solution):
        pass
    ## Return a new neighbor solution
    def neighbor(self, solution):
        pass
    ## Return a probability to decide whether accpet or not.
    def acceptance_probability(self, old_cost, new_cost, temperature):
        pass
    ## Start annealing
    def anneal(self):
        pass

class TSPSolution(SAImpl):
    def __init__(self, city_info):
        SAImpl.__init__(self)
        self.city_info = city_info

        self.temperature = 1000.0
        self.alpha = 0.9
        self.terminate_temperature = 0.00001
        self.iterations = 500
    
    @staticmethod
    def get_init_params():
        num_cities = 20
        random.seed()
        city_ids = list(range(0, num_cities))
        city_info = {city_id: (random.random() * 100, random.random() * 100) for city_id in city_ids}
        return city_info

    ## For TSP, we calculate the total distance between all cities.
    def cost(self, solution):
        total = len(self.city_info.keys())
        cost = 0
        for index, cid in enumerate(solution):
            first_city = cid
            next_city = solution[(index + 1) % total]

            cost += calc_linear_distance(self.city_info[first_city][0], self.city_info[first_city][1],
                                         self.city_info[next_city][0], self.city_info[next_city][1])
        return cost
    
    ## Find a neighbor solution by swapping random two nodes.
    def neighbor(self, solution):
        neighbor = solution[:]
        total = len(self.city_info.keys())
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
        solution = list(self.city_info.keys())
        random.shuffle(solution)

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

        plot_tsp_result(self.city_info, solution)
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
        pass

sa = SimulatedAnnealing(TSPSolution)
sa.anneal()