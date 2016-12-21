#ifndef __oclga_shuffler_chromosome__
#define __oclga_shuffler_chromosome__

#include "ga_utils.c"

void dump_chromosomes(global __ShufflerChromosome* chromosomes,
                      global float* fitnesses)
{
  int idx = get_global_id(0);
  if (idx > 0) {
    return;
  }
  for (int i = 0; i < CHROMOSOME_SIZE; i++) {
    __ShufflerChromosome chromosome = chromosomes[i];
    printf("Chromosome[%d]/dist[%f]:", i, fitnesses[i]);
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

void shuffler_chromosome_mutate(global __ShufflerChromosome* chromosome, float prob_mutate,
                                uint* rand_holder)
{
  for (int i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
    float prob_m =  rand_prob(rand_holder);
    if (prob_m <= prob_mutate) {
      uint j = rand_range_exclude(rand_holder, SHUFFLER_CHROMOSOME_GENE_SIZE, i);
      shuffler_chromosome_swap(chromosome, i, j);
    }
  }
}


void shuffler_chromosome_single_gene_mutate(global __ShufflerChromosome* chromosome,
                                            float prob_mutate,
                                            uint* rand_holder)
{
  float prob_m =  rand_prob(rand_holder);
  if (prob_m > prob_mutate) {
    return;
  }
  uint i = rand_range(rand_holder, SHUFFLER_CHROMOSOME_GENE_SIZE);
  uint j = rand_range_exclude(rand_holder, SHUFFLER_CHROMOSOME_GENE_SIZE, i);
  shuffler_chromosome_swap(chromosome, i, j);
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

void shuffler_chromosome_update_survivors(int idx,
                                          global float* fitnesses,
                                          global float* global_best,
                                          global float* global_weakest,
                                          int num_of_chromosomes,
                                          global bool* survivors)
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
}

// ============================ method 2 ===========================

void shuffler_chromosome_calc_ratio(global float* fitness,
                                    float* ratio,
                                    float* min_local,
                                    float* max_local)
{
  *min_local = INT_MAX;
  *max_local = 0;
  calc_min_max_fitness(fitness, POPULATION_SIZE, min_local, max_local);
  float diff[POPULATION_SIZE];
  float diffTotal = 0;
  int i;
  // we use total and diff to calculate the probability for each chromosome
  for (i = 0; i < POPULATION_SIZE; i++) {
    diff[i] = (*max_local - fitness[i]) * (*max_local - fitness[i]);
    diffTotal += diff[i];
  }
  // calculate probability for each one
  for (i = 0; i < POPULATION_SIZE; i++) {
    ratio[i] = diff[i] / diffTotal;
  }
}

int shuffler_chromosome_random_choose(global __ShufflerChromosome* chromosomes,
                                      float* ratio,
                                      uint* ra)
{

  // generate a random number from between 0 and 1
  float rand_choose = rand_prob(ra);
  int cross_idx = -1;
  // random choose a chromosome based on probability of each chromosome.
  while(rand_choose > 0.00001) {
    cross_idx++;
    rand_choose -= ratio[cross_idx];
  }
  return cross_idx;
}

void shuffler_chromosome_pick_chromosomes(int idx,
                                          global __ShufflerChromosome* chromosomes,
                                          global float* fitness,
                                          __ShufflerChromosome* parent1,
                                          __ShufflerChromosome* parent2,
                                          float* min_local,
                                          float* max_local,
                                          uint* ra)
{
  float ratio[POPULATION_SIZE];
  shuffler_chromosome_calc_ratio(fitness, ratio, min_local, max_local);
  int cross_idx = shuffler_chromosome_random_choose(chromosomes, ratio, ra);
  // copy the chromosome to local memory for cross over
  for (int i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
    // printf("[%d] p1->gene[%d] = %d, chromosomes[%d].gene[%d] = %d \n",
      // idx, i, parent1->genes[i], cross_idx, i, chromosomes[cross_idx].genes[i]);
    parent1->genes[i] = chromosomes[cross_idx].genes[i];
    // printf("[%d] p2->gene[%d] = %d, chromosomes[%d].gene[%d] = %d \n",
      // idx, i, parent2->genes[i], idx, i, chromosomes[idx].genes[i]);
    parent2->genes[i] = chromosomes[idx].genes[i];

  }
}

void shuffler_chromosome_do_crossover(int idx,
                                      global __ShufflerChromosome* chromosomes,
                                      __ShufflerChromosome* parent1,
                                      __ShufflerChromosome* parent2,
                                      uint* ra)
{
  int i;
  // we must be cross over at least one element and must not cross over all of the element.
  int cross_point = rand_range(ra, SHUFFLER_CHROMOSOME_GENE_SIZE - 1) + 1;
  int cross_map[SHUFFLER_CHROMOSOME_GENE_SIZE];
  for (i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
    cross_map[i] = 0;
  }
  // copy the first part from parent1
  for (i = 0; i < cross_point; i++) {
    chromosomes[idx].genes[i] = parent1->genes[i];
    cross_map[parent1->genes[i]] = 1;
  }
  // sort the second part at parent 2
  for (i = 0; i < SHUFFLER_CHROMOSOME_GENE_SIZE; i++) {
    if (cross_map[parent2->genes[i]] == 0) {
        chromosomes[idx].genes[cross_point++] = parent2->genes[i];
    }
  }
}

void shuffler_chromosome_two_item_crossover(int idx,
                                            global __ShufflerChromosome* chromosomes,
                                            global float* fitness,
                                            global bool* survivors,
                                            global float* best_global,
                                            global float* weakest_global,
                                            float prob_crossover,
                                            uint* ra)
{
  float max_local;
  float min_local;

  __ShufflerChromosome parent1;
  __ShufflerChromosome parent2;
  shuffler_chromosome_pick_chromosomes(idx, chromosomes, fitness, &parent1, &parent2,
                                       &min_local, &max_local, ra);

  barrier(CLK_GLOBAL_MEM_FENCE);
  // keep the shortest path, we have to return here to prevent async barrier if someone is returned.
  if (rand_prob(ra) >= prob_crossover || fitness[idx] - min_local < 0.0001) {
    // printf("best fitness: %f\n", fitness[idx]);
    return;
  }

  shuffler_chromosome_do_crossover(idx, chromosomes, &parent1, &parent2, ra);

  shuffler_chromosome_check_duplicate(chromosomes + idx);
}

#endif
