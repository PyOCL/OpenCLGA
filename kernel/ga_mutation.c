#include "ga_utils.c"

void mutate_by_swapping(int idx, int size_of_chromosome, global int* chromosomes,
                        float prob_mutate, uint* rand_holder)
{
  for (int i = 0; i < size_of_chromosome; i++) {
    float prob_m =  rand_prob(rand_holder);
    if (prob_m < prob_mutate) {
      uint j = rand_range_exclude(rand_holder, size_of_chromosome, i);
      chromosome_swap(idx, chromosomes, size_of_chromosome, i, j);
    }
  }
}

void mutate_natrual(int idx, int size_of_chromosome,
                    global int* gene_elements, int len_of_gene_elements,
                    global int* chromosomes,
                    float prob_mutate, uint* rand_holder)
{
  int s = idx * size_of_chromosome;
  for (int i = 0; i < size_of_chromosome; i++) {
    float prob_m =  rand_prob(rand_holder);
    if (prob_m < prob_mutate) {
      uint new_element_idx = rand_range(rand_holder, len_of_gene_elements);
      chromosomes[s+i] = gene_elements[new_element_idx];
    }
  }
}

void mutate(int idx, int size_of_chromosome, int num_of_chromosomes,
            global int* gene_elements, int len_of_gene_elements,
            global int* chromosomes, float prob_mutate, uint* rand_holder)
{
  mutate_by_swapping(idx, size_of_chromosome, chromosomes, prob_mutate, rand_holder);
  // mutate_natrual(idx, size_of_chromosome, gene_elements, len_of_gene_elements,
  //                chromosomes, prob_mutate, rand_holder)
}
