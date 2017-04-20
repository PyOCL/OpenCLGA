#ifndef __oclga_simple_chromosome__
#define __oclga_simple_chromosome__

#include "ga_utils.cl"

typedef struct {
  int genes[SIMPLE_CHROMOSOME_GENE_SIZE];
} __SimpleChromosome;

/* ============== populate functions ============== */
/**
 * simple_chromosome_do_populate populates a chromosome randomly. Unlike shuffler chromosome, it
 * chooses a gene randomly based on gene's element.
 * @param *chromosome (global, out) the target chromosome.
 * @param *rand_holder the random seed holder.
 */
void simple_chromosome_do_populate(global __SimpleChromosome* chromosome,
                                   uint* rand_holder)
{
  uint gene_elements_size[] = SIMPLE_CHROMOSOME_GENE_ELEMENTS_SIZE;
  for (int i = 0; i < SIMPLE_CHROMOSOME_GENE_SIZE; i++) {
    // choose an element randomly based on each gene's element size.
    chromosome->genes[i] = rand_range(rand_holder, gene_elements_size[i]);
  }
}

/**
 * simple_chromosome_populate populates all chromosomes randomly.
 * Note: this is a kernel function and will be called by python.
 * @param *cs (global, out) all chromosomes where population to be stored.
 * @param *input_rand (global) random seeds.
 */
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
/* ============== end of populating functions ============== */

/* ============== mutation functions ============== */
/**
 * mutate a single gene of a chromosome.
 * @param *chromosome (global) the chromosome for mutation.
 * @param *ra random seed holder.
 */
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
/**
 * mutate a single gene of all chromosomes based on the prob_mutate. If a
 * chromosome pass the probability, a single gene of it will be mutated.
 * @param *chromosome (global) the chromosome for mutation.
 * @param *ra (global) random seed holder.
 * @param prob_mutate the probability of mutation.
 */
__kernel void simple_chromosome_mutate(global int* cs,
                                       global uint* input_rand,
                                       float prob_mutate)
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

/**
 * mutate all genes of all chromosomes based on the prob_mutate. Once a
 * chromosome passes the probability, all genes of it will be mutated.
 * @param *chromosome (global) the chromosome for mutation.
 * @param *ra (global) random seed holder.
 * @param prob_mutate the probability of mutation.
 */
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
/* ============== end of mutation functions ============== */

/* ============== crossover functions ============== */
/**
 * simple_chromosome_calc_ratio uses utils_calc_ratio to find the best, worst,
 * avg fitnesses among all chromosomes the probability for each chromosomes
 * based on their fitness value.
 * Note: this is a kernel function and will be called by python.
 * @param *fitness (global) the fitness value array of all chromosomes
 * @param *ratio (global, out) the probability array of each chromosomes
 * @seealso ::utils_calc_ratio
 */
__kernel void simple_chromosome_calc_ratio(global float* fitness,
                                           global float* ratio)
{
  int idx = get_global_id(0);
  // we use the first kernel to calculate the ratio
  if (idx > 0) {
    return;
  }
  utils_calc_ratio(fitness, ratio, POPULATION_SIZE);
}

/**
 * simple_chromosome_pick_chromosomes picks a chromosome randomly based on the
 * ratio of each chromosome and copy all genes to p_other for crossover. The
 * reason copy to p_other is that OpenCLGA runs crossover at multi-thread mode.
 * The picked chromosomes may also be modified at the same time while crossing
 * over. If we don't copy them, we may have duplicated genes in a chromosome.
 * Note: this is a kernel function and will be called by python.
 * @param *cs (global) all chromosomes
 * @param *fitness (global) all fitness of chromosomes
 * @param *p_other (global) a spared space for storing another chromosome for
 *                          crossover.
 * @param *ratio (global) the ratio of all chromosomes.
 * @param *input_rand (global) all random seeds.
 */
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
  // Pick another chromosome as parent_other.
  int cross_idx = random_choose_by_ratio(ratio, ra, POPULATION_SIZE);
  // copy the chromosome to local memory for cross over
  for (i = 0; i < SIMPLE_CHROMOSOME_GENE_SIZE; i++) {
    other[idx].genes[i] = chromosomes[cross_idx].genes[i];
  }
  input_rand[idx] = ra[0];
}

/**
 * simple_chromosome_do_crossover does crossover for all chromosomes.
 * If a chromosomes passes the prob_crossover, we pick another chromosome for
 * crossover, see simple_chromosome_pick_chromosomes for more information. The
 * crossover procedure copys a range of genes from parent 2(p_other) to
 * parent 1(cs), like:
 * CS1 |----------------------------------|
 *        |start (copy from parent 2)  |end
 *        |^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
 * CS2 |----------------------------------|
 */
__kernel void simple_chromosome_do_crossover(global int* cs,
                                             global float* fitness,
                                             global int* p_other,
                                             global uint* input_rand,
                                             float best_fitness,
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
  if (fabs(fitness[idx] - best_fitness) < 0.000001) {
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
/* ============== end of crossover functions ============== */
/* ============== elitism ================================= */
/**
 * simple_chromosome_get_the_elites get the elites which meet the best_fitness
 * Note: this is a kernel function and will be called by python.
 * @param top (global) the number of chromosomes in the indices.
 * @param *best_indices (global) the index list of top N best fitness chromosomes.
 * @param *cs (global) all chromosomes.
 * @param *elites (global) elite chromosomes.
 */
__kernel void simple_chromosome_get_the_elites(global float* best_indices,
                                               global int* cs,
                                               global int* elites,
                                               int top)
{
  int idx = get_global_id(0);
  // we use the first kernel to get the best chromosome for now.
  if (idx > 0) {
    return;
  }
  int i;
  int j;
  int index;
  global __SimpleChromosome* chromosomes = (global __SimpleChromosome*) cs;
  global __SimpleChromosome* elites_chromosome = (global __SimpleChromosome*) elites;
  for (i = 0; i < top; i++) {
    index = best_indices[i];
    for (j = 0; j < SIMPLE_CHROMOSOME_GENE_SIZE; j++) {
      elites_chromosome[i].genes[j] = chromosomes[index].genes[j];
    }
  }
}

/**
 * simple_chromosome_update_the_elites update sorted elites into chromosomes.
 * Note: this is a kernel function and will be called by python.
 * @param top (local) the number of chromosomes in the indices.
 * @param *worst_indices (global) the index list of bottom N worst fitness chromosomes.
 * @param *cs (global) all chromosomes.
 * @param *fitnesses (global) fitnesses of all chromosomes
 * @param *elites (global) elite chromosomes.
 * @param *elite_fitnesses (global) fitnesses of all elite chromosomes.
 */
__kernel void simple_chromosome_update_the_elites(int top,
                                                  global int* worst_indices,
                                                  global int* cs,
                                                  global int* elites,
                                                  global float* fitnesses,
                                                  global float* elite_fitnesses)
{
  int idx = get_global_id(0);
  // we use the first kernel to update all elites and their fitnesses.
  if (idx > 0) {
    return;
  }
  int i;
  int j;
  int index;
  global __SimpleChromosome* chromosomes = (global __SimpleChromosome*) cs;
  global __SimpleChromosome* elites_chromosome = (global __SimpleChromosome*) elites;
  for (i = 0 ; i < top; i++) {
    index = worst_indices[i];
    for (j = 0; j < SIMPLE_CHROMOSOME_GENE_SIZE; j++) {
      chromosomes[index].genes[j] = elites_chromosome[i].genes[j];
    }
    fitnesses[index] = elite_fitnesses[index];
  }
}
/* ============== end of elitism functions ============== */
#endif
