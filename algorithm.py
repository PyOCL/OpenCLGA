import sys
import time
import random
from abc import ABC, abstractmethod
from chromosome import Chromosome

class BaseGeneticAlgorithm(ABC):
    def __init__(self, chromosomes):
        assert all(isinstance(chromosome, Chromosome) for chromosome in chromosomes)
        self.__chromosomes = chromosomes
        self.__population_size = len(chromosomes)
        self.elapsed_time = None
        self.__chromosome_to_fitness = {}
        self.__c_run_func = self.__run_impl
        self.__c_co_func = Chromosome.crossover
        self.__c_mu_func = Chromosome.mutate

        self.best = None
        self.best_fitness =  -sys.maxsize
        self.weakest = None
        self.weakest_fitness = sys.maxsize

        self.count = 0
        self.eval_time = 0

    def get_avg_evaluation_time(self):
        return self.eval_time / float(self.count)

    def __get_now_best(self):
        return max(self.__chromosome_to_fitness.items(), key=(lambda x: x[1]))

    def __get_now_weakest(self):
        return min(self.__chromosome_to_fitness.items(), key=(lambda x: x[1]))

    def __select(self, chromosomes):
        threshold_fit = self.weakest_fitness + (self.best_fitness - self.weakest_fitness) / 2

        survivors = []
        for chromosome in chromosomes:
            chromosome_fit = self.__chromosome_to_fitness[chromosome]
            if chromosome_fit >= threshold_fit:
                survivors.append(chromosome)

        return survivors if survivors else chromosomes

    def __reproduce(self, survivors, prob):
        num_survivors = len(survivors)
        offspring = []
        # Randomly choose 2 chromosomes to crossover
        while num_survivors + len(offspring) < self.__population_size:
            c1 = random.choice(survivors).clone()
            if random.random() < prob:
                c2 = random.choice(survivors).clone()
                crosspoint = random.randrange(0, c1.num_of_genes)
                self.__c_co_func(c1, c2, crosspoint)

            offspring.append(c1)

        assert (len(survivors) + len(offspring)) == self.__population_size
        return survivors + offspring

    def __start_mutation(self, prob):
        for chromosome in self.__chromosomes:
            self.__c_mu_func(chromosome, prob)

    def __calc_generation_fitness(self):
        self.__chromosome_to_fitness.clear();

        s = time.time()
        self.evaluate_fitness(self.__chromosomes)
        self.count += 1
        self.eval_time += time.time() - s

        now_best, now_best_fit = self.__get_now_best()
        now_weakest, now_weakest_fit = self.__get_now_weakest()

        if now_best_fit > self.best_fitness:
            self.best = now_best.clone()
            self.best_fitness = float(now_best_fit)
        if now_weakest_fit < self.weakest_fitness:
            self.weakest = now_weakest.clone()
            self.weakest_fitness = float(now_weakest_fit)

    def __run_impl(self, generations, prob_mutate, prob_crossover):
        self.__calc_generation_fitness()

        # Steps for each generation
        # 1 - select survivors
        # 2 - reproduce new individuals by crossover
        # 3 - mutate
        # 4 - calculate all chromosomes's fitness
        for gen in range(1, generations + 1):
            survivors = self.__select(self.__chromosomes)
            self.__chromosomes = self.__reproduce(survivors, prob_crossover)
            self.__start_mutation(prob_mutate)
            self.__calc_generation_fitness()
        pass

    def run(self, generations, prob_mutate, prob_crossover):
        # This function is not supposed to be overriden
        assert 0 <= prob_mutate <= 1
        assert 0 <= prob_crossover <= 1
        start_time = time.time()
        self.__c_run_func(generations, prob_mutate, prob_crossover)
        self.elapsed_time = time.time() - start_time

    def get_best(self):
        return self.best

    def get_best_fitness(self):
        return self.best_fitness

    def get_chromosomes(self):
        return self.__chromosomes

    @abstractmethod
    def evaluate_fitness(self, chromosomes):
        raise NotImplementedError

    def update_chromosome_fitness(self, chromosome, fitness):
        # This should be called in an overriden |evaluate_fitness|.
        self.__chromosome_to_fitness[chromosome] = fitness

    def set_customized_run_impl(self, func):
        self.__c_run_func = func

    def set_customized_crossover_func(self, func):
        self.__c_co_func = func

    def set_customized_mutate_func(self, func):
        self.__c_mu_func = func
