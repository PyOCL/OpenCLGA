import numpy
import pyopencl as cl

from simple_gene import SimpleGene
from shuffler_chromosome import ShufflerChromosome

class ShufflerChromosomeMethod2(ShufflerChromosome):
    # ShufflerChromosome - a chromosome contains a list of Genes.
    # __genes - an ordered list of Genes
    # __name - name of the chromosome
    # dna - an listed of Gene's dna
    # dna_total_length - sum of the lenght of all genes's dna
    def __init__(self, genes, name=""):
        ShufflerChromosome.__init__(self, genes, name)

    @property
    def kernel_file(self):
        return "shuffler_chromosome_method_2.c"

    def preexecute_kernels(self, ctx, queue, population):
        ## initialize global variables for kernel execution
        total_dna_size = population * self.dna_total_length

        other_chromosomes = numpy.zeros(total_dna_size, dtype=numpy.int32)
        cross_map = numpy.zeros(total_dna_size, dtype=numpy.int32)
        ratios = numpy.zeros(population, dtype=numpy.float32)
        best_fit = [0]
        weakest_fit = [0]

        mf = cl.mem_flags

        self.__dev_ratios = cl.Buffer(ctx, mf.WRITE_ONLY, ratios.nbytes)
        self.__dev_best = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                    hostbuf=numpy.array(best_fit, dtype=numpy.float32))
        self.__dev_weakest = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                       hostbuf=numpy.array(weakest_fit, dtype=numpy.float32))
        self.__dev_other_chromosomes = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                                 hostbuf=other_chromosomes)
        self.__dev_cross_map = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                         hostbuf=cross_map)

    def get_populate_kernel_names(self):
        return ["shuffler_chromosome_populate"]

    def get_crossover_kernel_names(self):
        return ["shuffler_chromosome_calc_ratio",\
                "shuffler_chromosome_pick_chromosomes",\
                "shuffler_chromosome_do_crossover"]

    def get_mutation_kernel_names(self):
        return ["shuffler_chromosome_single_gene_mutate"]

    def execute_populate(self, prg, queue, population, dev_chromosomes, dev_rnum):
        prg.shuffler_chromosome_populate(queue,
                                         (population,),
                                         (1,),
                                         dev_chromosomes,
                                         dev_rnum).wait()

    def execute_crossover(self, prg, queue, population, generation_idx, prob_crossover,
                          dev_chromosomes, dev_fitnesses, dev_rnum):
        prg.shuffler_chromosome_calc_ratio(queue,
                                           (1,),
                                           (1,),
                                           dev_fitnesses,
                                           self.__dev_ratios,
                                           self.__dev_best,
                                           self.__dev_weakest).wait()
        prg.shuffler_chromosome_pick_chromosomes(queue,
                                                 (population,),
                                                 (1,),
                                                 dev_chromosomes,
                                                 dev_fitnesses,
                                                 self.__dev_other_chromosomes,
                                                 self.__dev_ratios,
                                                 dev_rnum).wait()
        prg.shuffler_chromosome_do_crossover(queue,
                                             (population,),
                                             (1,),
                                             dev_chromosomes,
                                             dev_fitnesses,
                                             self.__dev_other_chromosomes,
                                             self.__dev_cross_map,
                                             self.__dev_best,
                                             numpy.float32(prob_crossover),
                                             dev_rnum).wait()


    def execute_mutation(self, prg, queue, population, generation_idx, prob_mutate,
                         dev_chromosomes, dev_fitnesses, dev_rnum):
        prg.shuffler_chromosome_single_gene_mutate(queue,
                                                   (population,),
                                                   (1,),
                                                   dev_chromosomes,
                                                   numpy.float32(prob_mutate),
                                                   dev_rnum).wait()
