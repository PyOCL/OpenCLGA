#ifndef __oclga_simple_chromosome__
#define __oclga_simple_chromosome__

#include "ga_utils.cl"

typedef struct {
  int genes[SIMPLE_CHROMOSOME_GENE_SIZE];
} __SimpleChromosome;

/* ============== populate functions ============== */
// functions for populate
void simple_chromosome_do_populate(global __SimpleChromosome* chromosome,
                                   uint* rand_holder)
{
  uint gene_elements_size[] = SIMPLE_CHROMOSOME_GENE_ELEMENTS_SIZE;
  for (int i = 0; i < SIMPLE_CHROMOSOME_GENE_SIZE; i++) {
    chromosome->genes[i] = rand_range(rand_holder, gene_elements_size[i]);
  }
}

__kernel void simple_chromosome_populate(global int* cs,
                                         global uint* input_rand)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }
  // create a private variable for each kernel to hold randome number.
  uint ra[1];
  init_rand(input_rand[idx], ra);
  simple_chromosome_do_populate(((global __SimpleChromosome*) cs) + idx,
                                ra);
  input_rand[idx] = ra[0];
}

/* ============== mutate functions ============== */

void simple_chromosome_do_mutate(global __SimpleChromosome* chromosome,
                                 uint* ra)
{
  // create element size list
  uint elements_size[] = SIMPLE_CHROMOSOME_GENE_ELEMENTS_SIZE;
  uint gene_idx = rand_range(ra, SIMPLE_CHROMOSOME_GENE_SIZE);
  // use gene's mutate function to mutate it.
  SIMPLE_CHROMOSOME_GENE_MUTATE_FUNC(chromosome->genes + gene_idx,
                                     elements_size[gene_idx], ra);
}

__kernel void simple_chromosome_mutate(global int* cs,
                                       float prob_mutate,
                                       global uint* input_rand)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }

  uint ra[1];
  init_rand(input_rand[idx], ra);
  float prob_m = rand_prob(ra);
  if (prob_m > prob_mutate) {
    input_rand[idx] = ra[0];
    return;
  }

  simple_chromosome_do_mutate((global __SimpleChromosome*) cs, ra);
}

// Chromosomes are picked by chance.
// The picked chromosome must mutate.
__kernel void simple_chromosome_mutate_all(global int* cs,
                                           global uint* input_rand,
                                           float prob_mutate)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }
  uint elements_size[] = SIMPLE_CHROMOSOME_GENE_ELEMENTS_SIZE;
  int i;
  uint ra[1];
  init_rand(input_rand[idx], ra);
  for (i = 0; i < SIMPLE_CHROMOSOME_GENE_SIZE; i++) {
    if (rand_prob(ra) > prob_mutate) {
      continue;
    }
    SIMPLE_CHROMOSOME_GENE_MUTATE_FUNC(cs + i, elements_size[i], ra);
  }

  input_rand[idx] = ra[0];
}

/* ============== crossover functions ============== */
// See comment for utils_calc_ratio()
__kernel void simple_chromosome_calc_ratio(global float* fitness,
                                           global float* ratio,
                                           global float* best,
                                           global float* worst,
                                           global float* avg)
{
  int idx = get_global_id(0);
  // we use the first kernel to calculate the ratio
  if (idx > 0) {
    return;
  }
  utils_calc_ratio(fitness, ratio, best, worst, avg, POPULATION_SIZE);
}

// Preparing another chromosomes array according to their fitness ratios.
// Then crossover by picking parent_1 from original chromosomes array and
// parent_2 from the newly-prepared chromosomes array.
__kernel void simple_chromosome_pick_chromosomes(global int* cs,
                                                 global float* fitness,
                                                 global int* p_other,
                                                 global float* ratio,
                                                 global uint* input_rand)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }
  uint ra[1];
  init_rand(input_rand[idx], ra);
  global __SimpleChromosome* chromosomes = (global __SimpleChromosome*) cs;
  global __SimpleChromosome* other = (global __SimpleChromosome*) p_other;
  int i;
  // Pick another chromosome as parent_2.
  int cross_idx = random_choose_by_ratio(ratio, ra, POPULATION_SIZE);
  // copy the chromosome to local memory for cross over
  for (i = 0; i < SIMPLE_CHROMOSOME_GENE_SIZE; i++) {
    other[idx].genes[i] = chromosomes[cross_idx].genes[i];
  }
  input_rand[idx] = ra[0];
}

// Pick 2 random cross-point index (start, end), then Parent 1(cs) and
// Parent 2(p_other) start crossover.
// CS1 |----------------------------------|
//           |start                |end
//           |=> to be exchanged <=|
// CS2 |----------------------------------|
__kernel void simple_chromosome_do_crossover(global int* cs,
                                             global float* fitness,
                                             global int* p_other,
                                             global float* best_local,
                                             global uint* input_rand,
                                             float prob_crossover)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }
  uint ra[1];
  init_rand(input_rand[idx], ra);

  // keep the shortest path, we have to return here to prevent async barrier
  // if someone is returned.
  if (fabs(fitness[idx] - *best_local) < 0.000001) {
    input_rand[idx] = ra[0];
    return;
  } else if (rand_prob(ra) >= prob_crossover) {
    input_rand[idx] = ra[0];
    return;
  }
  global __SimpleChromosome* chromosomes = (global __SimpleChromosome*) cs;
  global __SimpleChromosome* other = (global __SimpleChromosome*) p_other;
  int i;
  // keep at least one for .
  int start = rand_range(ra, SIMPLE_CHROMOSOME_GENE_SIZE - 1);
  int end = start + rand_range(ra, SIMPLE_CHROMOSOME_GENE_SIZE - start);
  // copy partial genes from other chromosome
  for (i = start; i < end; i++) {
    chromosomes[idx].genes[i] = other[idx].genes[i];
  }

  input_rand[idx] = ra[0];
}

#endif
