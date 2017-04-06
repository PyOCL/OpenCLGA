#!/usr/bin/python3
import os
import random
from OpenCLGA import OpenCLGA, SimpleChromosome, SimpleGene, utils

def show_generation_info(index, data_dict):
    print("{0}\t\t==> {1}".format(index, data_dict["best"]))

'''
In this example, we are trying to find the expansion of an algebra:
  (X + Y)^10 = aX^10 + bX^9Y + cX^8Y^2 ... + iX^2Y^8 + jXY^9 + kY^10

We have 11 unknown elements: a, b, c, d, e, f, g, h, i, j, k

The correct answer is: 1, 10, 45, 120, 210, 252, 210, 120, 45, 10, 1

The chromosome has 11 genes and each of them has value range from 0 to 252. The combination of this
question is 252^11. That is huge enough for GA. To have different types of gene, we change the value
range of each gene to different values, like:
gene 1: 1 ~ 10
gene 2: 1 ~ 20
gene 3: 1 ~ 50
gene 4: 1 ~ 150
gene 5: 1 ~ 250
gene 6: 1 ~ 300
gene 7: 1 ~ 250
gene 9: 1 ~ 150
gene 9: 1 ~ 50
gene 10: 1 ~ 20
gene 11: 1 ~ 10

The original problem space is: 260,259,114,966,540,661,762,818,048
The current problem space is:           42,187,500,000,000,000,000
'''
def run(num_chromosomes, generations):
    value_ranges = [10, 20, 50, 150, 250, 300, 250, 150, 50, 20, 10]

    sample = SimpleChromosome([SimpleGene(0, list(range(v))) for v in value_ranges])

    algebra_path = os.path.dirname(os.path.abspath(__file__))
    ocl_kernels = os.path.realpath(os.path.join(algebra_path, "..", "..", "kernel"))
    algebra_kernels = os.path.join(algebra_path, "kernel")

    f = open(os.path.join(algebra_kernels, "expansion.c"), "r")
    fstr = "".join(f.readlines())
    f.close()

    import threading
    evt = threading.Event()
    evt.clear()
    def run_end(paused):
        evt.set()

    ga_cl = OpenCLGA({"sample_chromosome": sample,
                      "termination": { "type": "count",
                                       "count": generations },
                      "population": num_chromosomes,
                      "fitness_kernel_str": fstr,
                      "fitness_func": "expansion_fitness",
                      "extra_include_path": [ocl_kernels],
                      "opt_for_max": "min",
                      "generation_callback": show_generation_info},
                      action_callbacks = {'run' : run_end})

    ga_cl.prepare()

    prob_mutate = 0.1
    prob_cross = 0.8
    ga_cl.run(prob_mutate, prob_cross)
    evt.wait()

    utils.plot_ga_result(ga_cl.get_statistics())
    print("run took", ga_cl.elapsed_time, "seconds")
    best_chromosome, best_fitness, best_info = ga_cl.get_the_best()
    print("Best Fitness: %f"%(best_fitness))
    print("Expansion of (x + y)^10 is: " + " ".join(str(g) for g in best_chromosome))

if __name__ == '__main__':
    run(num_chromosomes=10000, generations=500)
