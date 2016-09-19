import random
HUMAN_DNA_ELEMENTS = set(["A","C","G","T"])

def clone_gene(g):
    return Gene(g.dna, g.elements, g.name)

class Gene:
    # Gene - a sequence of DNAs.
    # dna - a list which contains items from elements.
    # elements - a set of element which is the basic component of dna.
    def __init__(self, dna, elements=HUMAN_DNA_ELEMENTS, name=""):
        assert type(dna) == list
        assert type(elements) == set
        self.__elements = elements
        self.__name = name
        self.__set_dna(dna)

    def __get_dna(self):
        return self.__dna

    def __set_dna(self, dna):
        assert type(dna) == list
        assert all(elem in self.__elements for elem in dna)
        self.__dna = dna

    def __get_dna_length(self):
        return len(self.__dna)

    def __get_gene_name(self):
        return self.__name

    def __get_gene_elements(self):
        return self.__elements

    dna = property(__get_dna, __set_dna)
    length = property(__get_dna_length)
    name = property(__get_gene_name)
    elements = property(__get_gene_elements)

    def mutate(self, prob=0.5):
        new_dna = []
        for elem in self.dna:
            if random.random() < prob:
                elem = random.choice(list(self.__elements.difference([elem])))
            new_dna.append(elem)
        self.dna = new_dna
