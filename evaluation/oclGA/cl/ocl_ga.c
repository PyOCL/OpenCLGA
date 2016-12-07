#include "ga_utils.c"

// Populate the first generation of chromosomes.
__kernel void ocl_ga_populate(global int* chromosomes, global int* input_rand)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }
  // create a private variable for each kernel to hold randome number.
  uint ra[1];
  init_rand(idx+input_rand[0], ra);
  POPULATE_FUNCTION(((global CHROMOSOME_TYPE*) chromosomes) + idx, ra);
}

__kernel void ocl_ga_evaluate(global int* chromosomes,
                              global float* fitness,
                              global bool* survivors,
                              global int* input_rand,
                              global float* best_global,
                              global float* weakest_global,
                              float prob_mutate,
                              float prob_crossover)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }
  // create a private variable for each kernel to hold randome number.
  uint ra[1];
  init_rand(idx + input_rand[0], ra);

  CALCULATE_FITNESS(((global CHROMOSOME_TYPE*) chromosomes) + idx, fitness + idx,
                    CHROMOSOME_SIZE, POPULATION_SIZE);
  // Barrier for the calculation of all chromosomes fitness.
  barrier(CLK_GLOBAL_MEM_FENCE);

  // NOTE: To print chromosomes for each round.
  // print_chromosomes(chromosomes, chromosome_size, chromosome_count, distances);
  // barrier(CLK_GLOBAL_MEM_FENCE);
  CROSSOVER(idx, (global CHROMOSOME_TYPE*) chromosomes, fitness, survivors, best_global,
            weakest_global, prob_crossover, ra);
  // Barrier for mutation, we need to make sure to reproduction for all chromosomes
  // is done to prevent mutation with weak chromosomes.
  barrier(CLK_GLOBAL_MEM_FENCE);

  MUTATE(((global CHROMOSOME_TYPE*) chromosomes) + idx, prob_mutate, ra);
}
