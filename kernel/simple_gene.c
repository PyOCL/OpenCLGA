#ifndef __oclga_simple_gene__
#define __oclga_simple_gene__

#include "ga_utils.c"


void simple_gene_mutate(global int* gene, uint max, uint* ra) {
  *gene = rand_range_exclude(ra, max, *gene);
}

#endif
