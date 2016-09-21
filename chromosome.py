from gene import Gene, clone_gene

def crossover(c1, c2, p1, p2=None):
    assert 0 <= p1 < c2.num_of_genes
    assert c2.num_of_genes == c1.num_of_genes
    if p2:
        assert 0 <= p2 < c2.num_of_genes
        assert p1 < p2
        c1_mid = c1.dna[p1:p2]
        c2_mid = c2.dna[p1:p2]
        c1.dna = c1.dna[:p1] + c2_mid + c1.dna[p2:]
        c2.dna = c2.dna[:p1] + c1_mid + c2.dna[p2:]
    else:
        c1_rear = c1.dna[p1:]
        c2_rear = c2.dna[p1:]
        c1.dna = c1.dna[:p1] + c2_rear
        c2.dna = c2.dna[:p1] + c1_rear

class Chromosome:
    # Chromosome - a much longer dna sequence containing many genes.
    # __genes - an ordered list of Genes
    # __name - name of the chromosome
    # dna - an listed of Gene's dna
    # dna_total_length - sum of the lenght of all genes's dna
    def __init__(self, genes, name=""):
        assert all(isinstance(gene, Gene) for gene in genes)
        self.__genes = genes
        self.__name = name

    def __get_number_of_genes(self):
        return len(self.__genes)

    def __get_name(self):
        return self.__name

    def __get_dna_total_length(self):
        length = 0
        for gene in self.__genes:
            length += gene.length
        return length

    def __get_dna(self):
        return [gene.dna for gene in self.__genes]

    def __set_dna(self, dna):
        assert self.num_of_genes == len(dna)
        for i, gene in enumerate(self.__genes):
            gene.dna = dna[i]

    name = property(__get_name)
    num_of_genes = property(__get_number_of_genes)
    dna_total_length = property(__get_dna_total_length)
    dna = property(__get_dna, __set_dna)

    def mutate(self, prob):
        assert 0 <= prob <= 1
        for gene in self.__genes:
            gene.mutate(prob)

    def clone(self):
        new_genes = [clone_gene(gene) for gene in self.__genes]
        return Chromosome(new_genes)

    def swap(self, p1, p2):
        assert 0 <= p1 < self.num_of_genes
        assert 0 <= p2 < self.num_of_genes
        tmp = self.__genes[p1]
        self.__genes[p1] = self.__genes[p2]
        self.__genes[p2] = tmp
        pass
