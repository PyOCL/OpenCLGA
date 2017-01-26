import random
HUMAN_DNA_ELEMENTS = ["A","C","G","T"]

class SimpleGene:

    @staticmethod
    def clone_gene(g):
        return SimpleGene(g.dna, g.elements, g.name)

    # SimpleGene - is a Gene with only one DNA.
    # dna - an object.
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
        return 1

    @property
    def name(self):
        return self.__name

    @property
    def elements(self):
        return self.__elements

    @property
    def elements_in_kernel(self):
        return list(range(0, len(self.__elements)))

    @property
    def kernel_file(self):
        return "simple_gene.c"

    def kernelize(self):
        elements_str = ", ".join([str(v) for v in self.elements_in_kernel])
        return "#define SIMPLE_GENE_ELEMENTS {" + elements_str + "}\n"

    def from_kernel_value(self, v):
        assert v > -1 and v < len(self.__elements)
        return SimpleGene(self.__elements[v], self.__elements, self.__name)
