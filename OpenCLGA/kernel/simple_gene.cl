#ifndef __oclga_simple_gene__
#define __oclga_simple_gene__

#include "ga_utils.cl"

/**
 * simle_gene_mutate mutates a single gene. Because we mapped the elements as
 * the index, we random select another index as the value of the gene.
 * @param *gene (global) the gene we need to mutate
 * @param max the size of elements.
 * @param *ra the random number holder.
 */
void simple_gene_mutate(global int* gene, uint max, uint* ra) {
  *gene = rand_range_exclude(ra, max, *gene);
}

#endif
