from simple_gene import SimpleGene

class ShufflerChromosome:
    kernel_file = "shuffler_chromosome.c"

    populate_function = "shuffler_chromosome_populate"
    crossover_function = "shuffler_chromosome_crossover"
    mutation_function = "shuffler_chromosome_mutate"
    struct_name = "__ShufflerChromosome"
    chromosome_size_define = "SHUFFLER_CHROMOSOME_GENE_SIZE"

    # ShufflerChromosome - a chromosome contains a list of Genes.
    # __genes - an ordered list of Genes
    # __name - name of the chromosome
    # dna - an listed of Gene's dna
    # dna_total_length - sum of the lenght of all genes's dna
    def __init__(self, genes, name=""):
        assert all(isinstance(gene, SimpleGene) for gene in genes)
        assert type(genes) == list
        self.__genes = genes
        self.__name = name

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

    def kernelize(self):
        candidates = self.__genes[0].kernelize()
        defines = "#define SHUFFLER_CHROMOSOME_GENE_SIZE " + str(self.num_of_genes) + "\n"
        typedef = "typedef struct {\n" +\
                  "  int genes[" + str(self.num_of_genes) + "];\n" +\
                  "} __ShufflerChromosome;\n"
        return candidates + defines + typedef
