#ifndef __oclga_simple_gene__
#define __oclga_simple_gene__

#include "ga_utils.c"


void simple_gene_mutate(global int* gene, uint max, float prob_mutate, uint* ra) {
  float prob_m =  rand_prob(ra);
  if (prob_m > prob_mutate) {
    return;
  }

  *gene = rand_range_exclude(ra, max, *gene);
}

#endif
