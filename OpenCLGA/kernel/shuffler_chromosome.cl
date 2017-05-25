#ifndef __oclga_shuffler_chromosome__
#define __oclga_shuffler_chromosome__

#include "ga_utils.cl"

/**
 * __ShufflerChromosome is a struct for accessing n gene.
 */
typedef struct {
  int genes[SHUFFLER_CHROMOSOME_GENE_SIZE];
} __ShufflerChromosome;

/**
 * During the development, we may found some bugs in our chromosomes. One of
 * them is our codes generate duplicated gene while crossing over or mutating.
 * This is not acceptable in shuffler chromosome.
 * This function, shuffler_chromosome_check_dup, checks if there is any
 * duplicated gene in a chromosome.
 * @param *chromosome (global) the pointer of a chromosome which wants to be
 *                             checked.
 */
void shuffler_chromosome_check_dup(global __ShufflerChromosome* chromosome) {
  for (int i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
    for (int j = i + 1; j < SHUFFLER_CHROMOSOME_GENE_SIZE; j++) {
      if (chromosome->genes[i] == chromosome->genes[j]) {
        printf("after chromosome element duplicated @%d, %d\n", i, j);
        return;
      }
    }
  }
}

/* ============== populating functions ============== */
/**
 * shuffler_chromosome_do_populate populates a chromosome randomly. Since this
 * is a shuffler chromosome, the elements index of a gene is the size of
 * chromosome. This function random shuffles the whole chromosome.
 * @param *chromosome (global) the chromosome we want to populate
 * @param *rand_holder the random value holder
 */
void shuffler_chromosome_do_populate(global __ShufflerChromosome* chromosome,
                                     uint* rand_holder) {
  int gene_elements[] = SIMPLE_GENE_ELEMENTS;
  int rndIdx;
  // The algorithm here is:
  // 1. random pick a index from 0 ~ size and moved to chromosome
  // 2. move the latest index to the picked index
  // 3. go back to 1 until end
  // 4. put the left element to the end of chromosome.
  for (int i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE - 1; i++) {
    rndIdx = rand_range(rand_holder, (SHUFFLER_CHROMOSOME_GENE_SIZE - i - 1));
    chromosome->genes[i] = gene_elements[rndIdx];
    gene_elements[rndIdx] = gene_elements[
                                SHUFFLER_CHROMOSOME_GENE_SIZE - i - 1];
  }
  chromosome->genes[SHUFFLER_CHROMOSOME_GENE_SIZE - 1] = gene_elements[0];
}

/**
 * shuffler_chromosome_populate populate chromosomes with random. The current
 * design is to generate a chromosome in a thread.
 * Note: this is a kernel function and will be called by python.
 * @param *chromosomes (global) all memory storage for populating chromosomes.
 * @param *input_rand (global) random seeds for all threads.
 */
__kernel void shuffler_chromosome_populate(global int* chromosomes,
                                           global uint* input_rand) {
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }
  // create a private variable for each kernel to hold randome number.
  uint ra[1];
  init_rand(input_rand[idx], ra);
  shuffler_chromosome_do_populate(((global CHROMOSOME_TYPE*) chromosomes) + idx,
                                  ra);
  input_rand[idx] = ra[0];
}
/* ============== end of populating functions ============== */

/* ============== mutation functions ============== */
/**
 * shuffler_chromosome_swap swaps two genes of a chromosome.
 * @param *chromosome (global) the chromosome whose genes are swapped.
 * @param p1 the position of gene 1
 * @param p2 the position of gene 2
 */
void shuffler_chromosome_swap(global __ShufflerChromosome* chromosome, int p1,
                              int p2)
{
  int temp_p = chromosome->genes[p1];
  chromosome->genes[p1] = chromosome->genes[p2];
  chromosome->genes[p2] = temp_p;
}

/**
 * the dummy improving function. An improving function is a help function for
 * hinting the better result for swapping the selected gene. Since this is a
 * user provided function, we only need to implement a dummy function here.
 * @param *chromosome (global) the chromosome for improving. Please note this
 *                             chromosome is in int array mode.
 * @param idx the position of a gene which will be swapped.
 * @param chromosome_size the size of a chromosome.
 * @param FITNESS_ARGS the fitness arguments from ocl_ga options.
 * @return the index of suggested position for swapping.
 */
int shuffler_chromosome_dummy_improving_func(global int* chromosome,
                                             int idx,
                                             int chromosome_size FITNESS_ARGS)
{
  return 0;
}

/**
 * shuffler_chromosome_single_gene_mutate does the mutation of all chromosomes.
 *
 * Note: this is a kernel function and will be called by python.
 * @param *cs (global) all chromosomes.
 * @param *input_rand (global) random seeds array for all threads.
 * @param prob_mutate the threshold for mutation.
 * @param improve a flag to say if we need to call improving function.
 * @param FITNESS_ARGS the fitness arguments from ocl_ga options for improving
 *                     function.
 */
__kernel void shuffler_chromosome_single_gene_mutate(global int* cs,
                                                     global uint* input_rand,
                                                     float prob_mutate,
                                                     int improve FITNESS_ARGS)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }
  // prepare random number for current thread
  uint ra[1];
  init_rand(input_rand[idx], ra);
  // generate a probability for mutation
  float prob_m =  rand_prob(ra);
  if (prob_m > prob_mutate) {
    // no need to mutate
    input_rand[idx] = ra[0];
    return;
  }
  global __ShufflerChromosome* chromosomes = (global __ShufflerChromosome*) cs;
  // choose a position for mutation randomly.
  uint i = rand_range(ra, SHUFFLER_CHROMOSOME_GENE_SIZE);
  uint j;
  if (improve == 1) {
    // we only gives global int* type to IMPROVED_FITNESS_FUNC instead of
    // __ShufflerChromosome
    j = IMPROVED_FITNESS_FUNC((global int*)(chromosomes + idx), i,
                              SHUFFLER_CHROMOSOME_GENE_SIZE FITNESS_ARGV);
    if (i != j) {
      shuffler_chromosome_swap(chromosomes + idx, i, j);
    }
  } else {
    j = rand_range_exclude(ra, SHUFFLER_CHROMOSOME_GENE_SIZE, i);
    shuffler_chromosome_swap(chromosomes + idx, i, j);
  }
  input_rand[idx] = ra[0];
  shuffler_chromosome_check_dup(chromosomes + idx);
}
/* ============== end of mutation functions ============== */

/* ============== crossover functions ============== */
/**
 * shuffler_chromosome_calc_ratio uses utils_calc_ratio to find the best, worst,
 * avg fitnesses among all chromosomes the probability for each chromosomes
 * based on their fitness value.
 * Note: this is a kernel function and will be called by python.
 * @param *fitness (global) the fitness value array of all chromosomes
 * @param *ratio (global, out) the probability array of each chromosomes
 * @seealso ::utils_calc_ratio
 */
__kernel void shuffler_chromosome_calc_ratio(global float* fitness,
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
 * shuffler_chromosome_get_the_elites get the elites which meet the
 * best_fitness
 * Note: this is a kernel function and will be called by python.
 * @param top (global) the number of chromosomes in the indices.
 * @param *best_indices (global) the index list of top N best fitness chromosomes.
 * @param *cs (global) all chromosomes.
 * @param *elites (global) elite chromosomes.
 */
__kernel void shuffler_chromosome_get_the_elites(global float* best_indices,
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
  global __ShufflerChromosome* chromosomes = (global __ShufflerChromosome*) cs;
  global __ShufflerChromosome* elites_chromosome = (global __ShufflerChromosome*) elites;
  for (i = 0; i < top; i++) {
    index = best_indices[i];
    for (j = 0; j < SHUFFLER_CHROMOSOME_GENE_SIZE; j++) {
      elites_chromosome[i].genes[j] = chromosomes[index].genes[j];
    }
  }
}

/**
 * shuffler_chromosome_update_the_elites update sorted elites into
 * chromosomes.
 * Note: this is a kernel function and will be called by python.
 * @param top (local) the number of chromosomes in the indices.
 * @param *worst_indices (global) the index list of bottom N worst fitness chromosomes.
 * @param *cs (global) all chromosomes.
 * @param *fitnesses (global) fitnesses of all chromosomes
 * @param *elites (global) elite chromosomes.
 * @param *elite_fitnesses (global) fitnesses of all elite chromosomes.
 */
__kernel void shuffler_chromosome_update_the_elites(int top,
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
  global __ShufflerChromosome* chromosomes = (global __ShufflerChromosome*) cs;
  global __ShufflerChromosome* elites_chromosome = (global __ShufflerChromosome*) elites;
  for (i = 0 ; i < top; i++) {
    index = worst_indices[i];
    for (j = 0; j < SHUFFLER_CHROMOSOME_GENE_SIZE; j++) {
      chromosomes[index].genes[j] = elites_chromosome[i].genes[j];
    }
    fitnesses[index] = elite_fitnesses[i];
  }
}

/**
 * shuffler_chromosome_pick_chromosomes picks a chromosome randomly based on the
 * ratio of each chromosome and copy all genes to p_other for crossover. The
 * reason copy to p_other is that OpenCLGA runs crossover at multi-thread mode.
 * The picked chromosomes may also be modified at the same time while crossing
 * over. If we don't copy them, we may have duplicated genes in a chromosome.
 * Note: this is a kernel function and will be called by python.
 * @param *cs (global) all chromosomes
 * @param *fitness (global) all fitness of chromosomes
 * @param *p_other (global) a spared space for storing another chromosome for
 *                          crossover.
 * @param *input_rand (global) all random seeds.
 */
__kernel void shuffler_chromosome_pick_chromosomes(global int* cs,
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
  global __ShufflerChromosome* chromosomes = (global __ShufflerChromosome*) cs;
  global __ShufflerChromosome* parent_other = (global __ShufflerChromosome*) p_other;
  int i;
  // pick another chromosome randomly
  int cross_idx = random_choose_by_ratio(ratio, ra, POPULATION_SIZE);
  // copy the chromosome to local memory for crossover
  for (i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
    parent_other[idx].genes[i] = chromosomes[cross_idx].genes[i];
  }
  input_rand[idx] = ra[0];
}

/**
 * shuffler_chromosome_do_crossover do the crossover algorithm.
 * Note: this is a kernel function and will be called by python.
 * @param *cs (global) all chromosomes
 * @param *fitness (global) all fitness of chromosomes
 * @param *p_other (global) a spared space for storing another chromosome for
 *                          crossover.
 * @param *c_map (global) a temp int array for marking if a gene is already in
 *                        the chromosome.
 * @param *input_rand (global) all random seeds.
 * @param best_index the index of best fitness of all chromosomes.
 * @param prob_crossover the threshold of crossover.
 */
__kernel void shuffler_chromosome_do_crossover(global int* cs,
                                               global float* fitness,
                                               global int* p_other,
                                               global int* c_map,
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

  // keep the shortest path, we have to return here to prevent async barrier if someone is returned.
  if (fabs(fitness[idx] - best_fitness) < 0.000001) {
    input_rand[idx] = ra[0];
    return;
  } else if (rand_prob(ra) >= prob_crossover) {
    input_rand[idx] = ra[0];
    return;
  }
  global __ShufflerChromosome* chromosomes = (global __ShufflerChromosome*) cs;
  global __ShufflerChromosome* parent_other = (global __ShufflerChromosome*) p_other;
  // we use chromosome as a map object for checking the existence of Nth item.
  global __ShufflerChromosome* cross_map = (global __ShufflerChromosome*) c_map;
  __ShufflerChromosome self;
  int i;
  int cross_point;

  for (i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
    // copy self chromosome to local memory for cross over
    self.genes[i] = chromosomes[idx].genes[i];
    // reset the cross_map to 0
    cross_map[idx].genes[i] = 0;
  }

  // we must be cross over at least one element and must not cross over all of the element.
  cross_point = rand_range(ra, SHUFFLER_CHROMOSOME_GENE_SIZE - 1) + 1;

  // copy the first part from other chromosome
  for (i = 0; i < cross_point; i++) {
    chromosomes[idx].genes[i] = parent_other[idx].genes[i];
    cross_map[idx].genes[parent_other[idx].genes[i]] = 1;
  }
  // sort the second part at self chromosome
  for (i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
    if (cross_map[idx].genes[self.genes[i]] == 0) {
        chromosomes[idx].genes[cross_point++] = self.genes[i];
    }
  }
  shuffler_chromosome_check_dup(chromosomes + idx);
  input_rand[idx] = ra[0];
}
/* ============== end of crossover functions ============== */

#endif
