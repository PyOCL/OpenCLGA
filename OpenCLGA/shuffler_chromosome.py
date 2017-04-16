#!/usr/bin/python3
import numpy
import pyopencl as cl

from .simple_gene import SimpleGene

class ShufflerChromosome:
    # ShufflerChromosome - a chromosome contains a list of Genes.
    # __genes - an ordered list of Genes
    # __name - name of the chromosome
    # __improving_func - function name in kernel to gurantee a better mutation result.
    # dna - an listed of Gene's dna
    # dna_total_length - sum of the lenght of all genes's dna
    def __init__(self, genes, name = ''):
        assert all(isinstance(gene, SimpleGene) for gene in genes)
        assert type(genes) == list
        self.__genes = genes
        self.__name = name
        self.__improving_func = None

    @property
    def num_of_genes(self):
        return len(self.__genes)

    @property
    def name(self):
        return self.__name

    @property
    def dna_total_length(self):
        return self.num_of_genes

    @property
    def dna(self):
        return [gene.dna for gene in self.__genes]

    @dna.setter
    def dna(self, dna):
        assert self.num_of_genes == len(dna)
        for i, gene in enumerate(self.__genes):
            gene.dna = dna[i]

    @property
    def genes(self):
        return self.__genes

    @property
    def gene_elements(self):
        return [] if len(self.__genes) == 0 else self.__genes[0].elements

    @property
    def gene_elements_in_kernel(self):
        return [] if len(self.__genes) == 0 else self.__genes[0].elements_in_kernel

    @property
    def kernel_file(self):
        return 'shuffler_chromosome.cl'

    @property
    def struct_name(self):
        return '__ShufflerChromosome';

    @property
    def chromosome_size_define(self):
        return 'SHUFFLER_CHROMOSOME_GENE_SIZE'

    def early_terminated(self, best, worst):
        return False

    def from_kernel_value(self, data):
        assert len(data) == self.num_of_genes
        genes = [self.__genes[idx].from_kernel_value(v) for idx, v in enumerate(data)]
        return ShufflerChromosome(genes, self.__name)

    def use_improving_only_mutation(self, helper_func_name):
        self.__improving_func = helper_func_name

    def kernelize(self):
        improving_func = self.__improving_func if self.__improving_func is not None\
                                               else 'shuffler_chromosome_dummy_improving_func'
        candidates = '#define SIMPLE_GENE_ELEMENTS ' + self.__genes[0].elements_in_kernel_str
        defines = '#define SHUFFLER_CHROMOSOME_GENE_SIZE ' + str(self.num_of_genes) + '\n' +\
                  '#define IMPROVED_FITNESS_FUNC ' + improving_func + '\n'

        improving_func_header = 'int ' + improving_func + '(global int* c,' +\
                                'int idx,' +\
                                'int chromosome_size FITNESS_ARGS);'
        return candidates + defines + improving_func_header

    def save(self, data, ctx, queue, population):
        total_dna_size = population * self.dna_total_length
        # prepare memory
        other_chromosomes = numpy.zeros(total_dna_size, dtype=numpy.int32)
        cross_map = numpy.zeros(total_dna_size, dtype=numpy.int32)
        ratios = numpy.zeros(population, dtype=numpy.float32)
        # read data from cl
        cl.enqueue_read_buffer(queue, self.__dev_ratios, ratios)
        cl.enqueue_read_buffer(queue, self.__dev_other_chromosomes, other_chromosomes)
        cl.enqueue_read_buffer(queue, self.__dev_cross_map, cross_map).wait()
        # save all of them
        data['other_chromosomes'] = other_chromosomes
        data['cross_map'] = cross_map
        data['ratios'] = ratios

    def restore(self, data, ctx, queue, population):
        other_chromosomes = data['other_chromosomes']
        cross_map = data['cross_map']
        ratios = data['ratios']
        # build CL memory from restored memory
        mf = cl.mem_flags
        self.__dev_ratios = cl.Buffer(ctx, mf.WRITE_ONLY, ratios.nbytes)
        self.__dev_other_chromosomes = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                                 hostbuf=other_chromosomes)
        self.__dev_cross_map = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                         hostbuf=cross_map)

    def preexecute_kernels(self, ctx, queue, population):
        ## initialize global variables for kernel execution
        total_dna_size = population * self.dna_total_length

        other_chromosomes = numpy.zeros(total_dna_size, dtype=numpy.int32)
        cross_map = numpy.zeros(total_dna_size, dtype=numpy.int32)
        ratios = numpy.zeros(population, dtype=numpy.float32)

        mf = cl.mem_flags

        self.__dev_ratios = cl.Buffer(ctx, mf.WRITE_ONLY, ratios.nbytes)
        self.__dev_other_chromosomes = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                                 hostbuf=other_chromosomes)
        self.__dev_cross_map = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR,
                                         hostbuf=cross_map)

    def get_populate_kernel_names(self):
        return ['shuffler_chromosome_populate']

    def get_crossover_kernel_names(self):
        return ['shuffler_chromosome_calc_ratio',\
                'shuffler_chromosome_pick_chromosomes',\
                'shuffler_chromosome_do_crossover']

    def get_mutation_kernel_names(self):
        return ['shuffler_chromosome_single_gene_mutate']

    def execute_populate(self, prg, queue, population, dev_chromosomes, dev_rnum):
        prg.shuffler_chromosome_populate(queue,
                                         (population,),
                                         (1,),
                                         dev_chromosomes,
                                         dev_rnum).wait()

    def selection_preparation(self, prg, queue, dev_fitnesses,
                              dev_best, dev_worst, dev_avg):
        prg.shuffler_chromosome_calc_ratio(queue,
                                           (1,),
                                           (1,),
                                           dev_fitnesses,
                                           self.__dev_ratios,
                                           dev_best,
                                           dev_worst,
                                           dev_avg).wait()

    def execute_get_current_elites(self, prg, queue, top,
                                   dev_chromosomes, dev_current_elites,
                                   dev_best_indices):
        prg.get_the_elites(queue, (1,), (1,),
                           dev_best_indices,
                           dev_chromosomes,
                           dev_current_elites,
                           numpy.int32(top)).wait()

    def execute_update_current_elites(self, prg, queue, top,
                                      dev_chromosomes, dev_updated_elites,
                                      dev_worst):
        prg.update_the_elites(queue, (1,), (1,),
                              dev_worst,
                              dev_chromosomes,
                              dev_updated_elites,
                              numpy.int32(top)).wait()

    def execute_crossover(self, prg, queue, population, generation_idx, prob_crossover,
                          dev_chromosomes, dev_fitnesses, dev_rnum,
                          dev_best, dev_worst, dev_avg):
        prg.shuffler_chromosome_pick_chromosomes(queue,
                                                 (population,),
                                                 (1,),
                                                 dev_chromosomes,
                                                 dev_fitnesses,
                                                 self.__dev_other_chromosomes,
                                                 self.__dev_ratios,
                                                 dev_best,
                                                 dev_worst,
                                                 dev_rnum).wait()
        prg.shuffler_chromosome_do_crossover(queue,
                                             (population,),
                                             (1,),
                                             dev_chromosomes,
                                             dev_fitnesses,
                                             self.__dev_other_chromosomes,
                                             self.__dev_cross_map,
                                             dev_best,
                                             dev_worst,
                                             dev_avg,
                                             dev_rnum,
                                             numpy.float32(prob_crossover)).wait()


    def execute_mutation(self, prg, queue, population, generation_idx, prob_mutate,
                         dev_chromosomes, dev_fitnesses, dev_rnum, extra_list):

        args = [dev_chromosomes,
                dev_rnum,
                numpy.float32(prob_mutate),
                numpy.int32(self.__improving_func is not None)]
        args = args + extra_list
        prg.shuffler_chromosome_single_gene_mutate(queue,
                                            (population,),
                                            (1,),
                                            *args).wait()
