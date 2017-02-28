#ifndef __oclga_shuffler_chromosome__
#define __oclga_shuffler_chromosome__

#include "ga_utils.c"

typedef struct {
  int genes[SHUFFLER_CHROMOSOME_GENE_SIZE];
} __ShufflerChromosome;

void shuffler_chromosome_check_duplicate(global __ShufflerChromosome* chromosome) {
  for (int i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
    for (int j = i + 1; j < SHUFFLER_CHROMOSOME_GENE_SIZE; j++) {
      if (chromosome->genes[i] == chromosome->genes[j]) {
        printf("after chromosome element duplicated @%d, %d\n", i, j);
        return;
      }
    }
  }
}

// functions for populate
void shuffler_chromosome_do_populate(global __ShufflerChromosome* chromosome, uint* rand_holder) {
  int gene_elements[] = SIMPLE_GENE_ELEMENTS;
  int rndIdx;
  for (int i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE - 1; i++) {
    rndIdx = rand_range(rand_holder, (SHUFFLER_CHROMOSOME_GENE_SIZE - i - 1));
    chromosome->genes[i] = gene_elements[rndIdx];
    gene_elements[rndIdx] = gene_elements[SHUFFLER_CHROMOSOME_GENE_SIZE - i - 1];
  }
  chromosome->genes[SHUFFLER_CHROMOSOME_GENE_SIZE - 1] = gene_elements[0];
}

__kernel void shuffler_chromosome_populate(global int* chromosomes, global uint* input_rand) {
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }
  // create a private variable for each kernel to hold randome number.
  uint ra[1];
  init_rand(input_rand[idx], ra);
  shuffler_chromosome_do_populate(((global CHROMOSOME_TYPE*) chromosomes) + idx, ra);
  input_rand[idx] = ra[0];
}

// functions for mutation
void shuffler_chromosome_swap(global __ShufflerChromosome* chromosome, int cp, int p1)
{
  int temp_p = chromosome->genes[cp];
  chromosome->genes[cp] = chromosome->genes[p1];
  chromosome->genes[p1] = temp_p;
}

int shuffler_chromosome_dummy_improving_func(global int* chromosome,
                                             int idx,
                                             int chromosome_size FITNESS_ARGS)
{
  return 0;
}

__kernel void shuffler_chromosome_single_gene_mutate(global int* cs,
                                                     float prob_mutate,
                                                     global uint* input_rand,
                                                     int improve FITNESS_ARGS)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }

  uint ra[1];
  init_rand(input_rand[idx], ra);
  float prob_m =  rand_prob(ra);
  if (prob_m > prob_mutate) {
    input_rand[idx] = ra[0];
    return;
  }
  global __ShufflerChromosome* chromosomes = (global __ShufflerChromosome*) cs;
  uint i = rand_range(ra, SHUFFLER_CHROMOSOME_GENE_SIZE);
  uint j;
  if (improve == 1) {
    // we only gives global int* type to IMPROVED_FITNESS_FUNC instead of __ShufflerChromosome
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
  shuffler_chromosome_check_duplicate(chromosomes + idx);
}

__kernel void shuffler_chromosome_calc_ratio(global float* fitness,
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
  utils_calc_ratio(fitness, ratio, best, worst, avg, idx, POPULATION_SIZE);
}

__kernel void shuffler_chromosome_pick_chromosomes(global int* cs,
                                                   global float* fitness,
                                                   global int* p_other,
                                                   global float* ratio,
                                                   global float* best_local,
                                                   global float* worst_local,
                                                   global uint* input_rand)
{
  if (fabs(*worst_local - *best_local) < 0.00001) {
    return;
  }
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
  int cross_idx = random_choose_by_ratio(ratio, ra, POPULATION_SIZE);
  // copy the chromosome to local memory for cross over
  for (i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
    parent_other[idx].genes[i] = chromosomes[cross_idx].genes[i];
  }
  input_rand[idx] = ra[0];
}

__kernel void shuffler_chromosome_do_crossover(global int* cs,
                                               global float* fitness,
                                               global int* p_other,
                                               global int* c_map,
                                               global float* best_local,
                                               global float* worst_local,
                                               global float* avg_local,
                                               float prob_crossover,
                                               global uint* input_rand,
                                               int generation_idx)
{
  if (fabs(*worst_local - *best_local) < 0.00001) {
    return;
  }
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }
  uint ra[1];
  init_rand(input_rand[idx], ra);

  // keep the shortest path, we have to return here to prevent async barrier if someone is returned.
  if (fabs(fitness[idx] - *best_local) < 0.000001) {
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
  shuffler_chromosome_check_duplicate(chromosomes + idx);
  input_rand[idx] = ra[0];
}

#endif
