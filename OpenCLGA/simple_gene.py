#!/usr/bin/python3
import random
HUMAN_DNA_ELEMENTS = ["A","C","G","T"]

class SimpleGene:

    @staticmethod
    def clone_gene(g):
        # Clone a new gene containing the same dna symbol in g.
        return SimpleGene(g.dna, g.elements, g.name)

    # SimpleGene - is a Gene with only one DNA element.
    # dna - a single element picked from elements.
    # elements - a set of element which is the basic component of dna.
    def __init__(self, dna, elements=HUMAN_DNA_ELEMENTS, name=""):
        assert dna is not None
        assert type(elements) == list
        self.__elements = elements
        self.__name = name
        self.dna = dna

    @property
    def dna(self):
        return self.__dna

    @dna.setter
    def dna(self, dna):
        assert dna is not None
        self.__dna = dna

    @property
    def dna_in_kernel(self):
        return self._elements.index(self.dna)

    @property
    def length(self):
        # SimpleGene is designed to be only 1 dna element inside.
        return 1

    @property
    def name(self):
        # The name of this SimpleGene
        return self.__name

    @property
    def elements(self):
        # The list of dna elements.
        return self.__elements

    @property
    def elements_in_kernel(self):
        return list(range(0, len(self.__elements)))

    @property
    def kernel_file(self):
        # Kernel file which contains related operating functions for SimpleGene,
        # i.e. simple_gene_mutate()
        return "simple_gene.c"

    @property
    def elements_length(self):
        # The elements size of this SimpleGene.
        # Could be considered as the problem space represented by this SimpleGene.
        return len(self.__elements)

    @property
    def mutate_func_name(self):
        # Chromosome can use this function to execute built-in mutate function which choose an
        # excluded elments randomly.
        return "simple_gene_mutate"

    @property
    def elements_in_kernel_str(self):
        # Chromosome can use this function to declare elements array
        elements_str = ", ".join([str(v) for v in self.elements_in_kernel])
        return "{" + elements_str + "}\n"

    def from_kernel_value(self, v):
        # Construct a SimpleGene object on system memory according to
        # the calculated index values 'v' on opencl(device) memory.
        assert 0 <= v < len(self.__elements)
        return SimpleGene(self.__elements[v], self.__elements, self.__name)
