#ifndef __oclga_shuffler_chromosome__
#define __oclga_shuffler_chromosome__

#include "ga_utils.c"

// functions for populate
void shuffler_chromosome_populate(global __ShufflerChromosome* chromosome, uint* rand_holder) {
  int gene_elements[] = SIMPLE_GENE_ELEMENTS;
  int rndIdx;
  for (int i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE - 1; i++) {
    rndIdx = rand_range(rand_holder, (SHUFFLER_CHROMOSOME_GENE_SIZE - i - 1));
    chromosome->genes[i] = gene_elements[rndIdx];
    gene_elements[rndIdx] = gene_elements[SHUFFLER_CHROMOSOME_GENE_SIZE - i - 1];
  }
  chromosome->genes[SHUFFLER_CHROMOSOME_GENE_SIZE - 1] = gene_elements[0];
}

// functions for mutation
void shuffler_chromosome_swap(global __ShufflerChromosome* chromosome, int cp, int p1)
{
  int temp_p = chromosome->genes[cp];
  chromosome->genes[cp] = chromosome->genes[p1];
  chromosome->genes[p1] = temp_p;
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

void shuffler_chromosome_mutate(global __ShufflerChromosome* chromosome, float prob_mutate,
                                uint* rand_holder)
{
  for (int i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
    float prob_m =  rand_prob(rand_holder);
    if (prob_m < prob_mutate) {
      uint j = rand_range_exclude(rand_holder, SHUFFLER_CHROMOSOME_GENE_SIZE, i);
      shuffler_chromosome_swap(chromosome, i, j);
    }
  }
}

// functions for crossover: find_survied_idx, shuffler_chromosome_reproduce,
//                          shuffler_chromosome_crossover

int shuffler_chromosome_find_survied_idx(uint* ra, global bool* surviors, int chromosome_count)
{
  uint s_idx = rand_range(ra, chromosome_count);
  int runs = 0;
  // NOTE: Avoid infinite while loop
  while (runs < chromosome_count) {
    uint adj_s_idx = (s_idx + runs) >= chromosome_count ? runs : s_idx;
    if (surviors[adj_s_idx]) {
      return adj_s_idx;
    }
    runs++;
  }
  return s_idx;
}

void shuffler_chromosome_reproduce(int idx, global __ShufflerChromosome* chromosomes,
                                   global bool* survivors, int num_of_chromosomes,
                                   float prob_crossover, uint* ra)
{
  // NOTE: Only dead chromosome needs to be reproduced.
  if (survivors[idx]) {
    return;
  }

  uint c1_idx = shuffler_chromosome_find_survied_idx(ra, survivors, num_of_chromosomes);

  float prob =  rand_prob(ra);
  // printf(" >>>>> not live - idx(%d)/ c1idx(%d), prob(%f)\n", idx, c1_idx, p_v);
  if (prob <= prob_crossover) {
    for (int i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
      chromosomes[idx].genes[i] = chromosomes[c1_idx].genes[i];
    }

    uint c2_idx = shuffler_chromosome_find_survied_idx(ra, survivors, num_of_chromosomes);
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
  } else {
    for (int i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
      chromosomes[idx].genes[i] = chromosomes[c1_idx].genes[i];
    }
  }
}

void shuffler_chromosome_update_survivors(int idx, global float* fitnesses,
                      global float* global_best, global float* global_weakest,
                      int num_of_chromosomes, global bool* survivors)
{
  // NOTE: No need to calculate survivor list with all kernels.
  //       We use the first kernel to do it.
  if (idx != 0) {
    return;
  }
  float min_local[1];
  float max_local[1];
  min_local[0] = INT_MAX;
  max_local[0] = 0.0;
  calc_min_max_fitness(fitnesses, num_of_chromosomes, min_local, max_local);
  global_best[0] = min(min_local[0], global_best[0]);
  global_weakest[0] = max(max_local[0], global_weakest[0]);

  // Calculate surviors indice.
  // TODO: Tuning the threshold to get better surviors !
  float threshold = global_weakest[0] - (global_weakest[0] - global_best[0]) / 1.1;
  // printf("[Thresholde] (%f) / global_best(%f) / weakest_fitness(%f)\n",
    // threshold, global_best[0], global_weakest[0]);
  for (int i = 0; i < num_of_chromosomes; i++) {
    survivors[i] = fitnesses[i] <= threshold ? true : false;
  }
}

void shuffler_chromosome_crossover(int idx, global __ShufflerChromosome* chromosomes,
                                   global float* fitness, global bool* survivors,
                                   global float* best_global, global float* weakest_global,
                                   float prob_crossover, uint* ra)
{

  shuffler_chromosome_update_survivors(idx, fitness, best_global, weakest_global, POPULATION_SIZE,
                                       survivors);
  // Barrier for survivor list.
  barrier(CLK_GLOBAL_MEM_FENCE);

  shuffler_chromosome_reproduce(idx, chromosomes, survivors, POPULATION_SIZE, prob_crossover, ra);
}

#endif
