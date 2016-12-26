#ifndef __oclga_shuffler_chromosome__
#define __oclga_shuffler_chromosome__

#include "ga_utils.c"

typedef struct {
  int genes[SHUFFLER_CHROMOSOME_GENE_SIZE];
} __ShufflerChromosome;

void dump_chromosomes(global __ShufflerChromosome* chromosomes,
                      global float* fitnesses)
{
  int idx = get_global_id(0);
  if (idx > 0) {
    return;
  }
  for (int i = 0; i < POPULATION_SIZE; i++) {
    __ShufflerChromosome chromosome = chromosomes[i];
    if (fitnesses == NULL) {
      printf("Chromosome[%d]:", i);
    } else {
      printf("Chromosome[%d]/dist[%f]:", i, fitnesses[i]);
    }

    for (int j = 0; j < SHUFFLER_CHROMOSOME_GENE_SIZE; j++) {
        printf("->(%d)", chromosome.genes[j]);
    }
    printf("\n");
  }
  printf("\n");
}

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

__kernel void shuffler_chromosome_mutate(global int* cs, float prob_mutate,
                                         global uint* input_rand)
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

  for (int i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
    float prob_m =  rand_prob(ra);
    if (prob_m <= prob_mutate) {
      uint j = rand_range_exclude(ra, SHUFFLER_CHROMOSOME_GENE_SIZE, i);
      shuffler_chromosome_swap(chromosomes + idx, i, j);
    }
  }
  input_rand[idx] = ra[0];
}

// functions for crossover: find_survied_idx, shuffler_chromosome_reproduce,
//                          shuffler_chromosome_crossover

int shuffler_chromosome_find_survied_idx(uint* ra, int* surviors, int survivor_count)
{
  if (survivor_count == 0) {
    return -1;
  }
  return surviors[rand_range(ra, survivor_count)];
}

void shuffler_chromosome_reproduce(int idx, global __ShufflerChromosome* chromosomes,
                                   int* survivors, int survivor_count,
                                   int num_of_chromosomes, float prob_crossover, uint* ra)
{
  // NOTE: Only dead chromosome needs to be reproduced.
  if (survivors[idx]) {
    return;
  }

  uint c1_idx = shuffler_chromosome_find_survied_idx(ra, survivors, survivor_count);
  if (c1_idx == -1) {
    return;
  }
  // Clone the genes of survival chromosome to the dead one.
  for (int i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
    chromosomes[idx].genes[i] = chromosomes[c1_idx].genes[i];
  }

  float prob =  rand_prob(ra);
  if (prob <= prob_crossover) {
    uint c2_idx = shuffler_chromosome_find_survied_idx(ra, survivors, survivor_count);
    if (c2_idx == -1) {
      return;
    }
    if (c1_idx != c2_idx) {
      // do crossover here
      uint cross_point = rand_range(ra, SHUFFLER_CHROMOSOME_GENE_SIZE);
      for (int i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
        if (chromosomes[idx].genes[i] == chromosomes[c2_idx].genes[cross_point]
            && i != cross_point) {
          shuffler_chromosome_swap(chromosomes + idx, cross_point, i);
          break;
        }
      }
    }
  }
}

__kernel void shuffler_chromosome_update_survivors(global float* fitnesses,
                                                   global float* global_best,
                                                   global float* global_weakest,
                                                   global bool* survivors)
{
  int idx = get_global_id(0);
  // we use the first kernel to calculate the ratio
  if (idx > 0) {
    return;
  }
  float min_local[1];
  float max_local[1];
  min_local[0] = INT_MAX;
  max_local[0] = 0.0;
  calc_min_max_fitness(fitnesses, POPULATION_SIZE, min_local, max_local);
  global_best[0] = min(min_local[0], global_best[0]);
  global_weakest[0] = max(max_local[0], global_weakest[0]);

  // Calculate surviors indice.
  // TODO: Tuning the threshold to get better surviors !
  float threshold = global_weakest[0] - (global_weakest[0] - global_best[0]) / 1.1;
  // printf("[Thresholde] (%f) / global_best(%f) / weakest_fitness(%f)\n",
    // threshold, global_best[0], global_weakest[0]);
  for (int i = 0; i < POPULATION_SIZE; i++) {
    survivors[i] = fitnesses[i] <= threshold ? true : false;
  }
}

__kernel void shuffler_chromosome_crossover(global __ShufflerChromosome* chromosomes,
                                            global float* fitness,
                                            global bool* survivors,
                                            float prob_crossover,
                                            global uint* input_rand)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }

  uint ra[1];
  init_rand(input_rand[idx], ra);
  int survivor_count = 0;
  int survivor_indice[POPULATION_SIZE];
  for (int i = 0; i < POPULATION_SIZE; i++) {
    if (survivors[i]) {
      survivor_indice[survivor_count++] = i;
    }
  }

  if (!survivors[idx]) {
    shuffler_chromosome_reproduce(idx, chromosomes, survivor_indice, survivor_count,
                                  POPULATION_SIZE, prob_crossover, ra);
  }
  shuffler_chromosome_check_duplicate(chromosomes + idx);
  input_rand[idx] = ra[0];
}

#endif
