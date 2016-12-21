#include "ga_utils.c"

// Populate the first generation of chromosomes.
__kernel void ocl_ga_populate(global int* chromosomes,
                              global float* fitness,
                              FITNESS_ARGS
                              global int* input_rand)
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
  CALCULATE_FITNESS(FITNESS_ARGV ((global CHROMOSOME_TYPE*) chromosomes) + idx, fitness + idx,
                    CHROMOSOME_SIZE, POPULATION_SIZE);
}

__kernel void ocl_ga_evaluate(global int* chromosomes,
                              global float* fitness,
                              global bool* survivors,
                              global int* input_rand,
                              global float* best_global,
                              global float* weakest_global,
                              FITNESS_ARGS
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

  // NOTE: To print chromosomes for each round.
  // dump_chromosomes((global CHROMOSOME_TYPE*) chromosomes, fitness);
  CROSSOVER(idx, (global CHROMOSOME_TYPE*) chromosomes, fitness, survivors, best_global,
            weakest_global, prob_crossover, ra);
  // Barrier for mutation, we need to make sure to reproduction for all chromosomes
  // is done to prevent mutation with weak chromosomes.
  barrier(CLK_GLOBAL_MEM_FENCE);
  // dump_chromosomes((global CHROMOSOME_TYPE*) chromosomes, fitness);
  MUTATE(((global CHROMOSOME_TYPE*) chromosomes) + idx, prob_mutate, ra);

  // Barrier for the calculation of all chromosomes fitness.
  barrier(CLK_GLOBAL_MEM_FENCE);
  // dump_chromosomes((global CHROMOSOME_TYPE*) chromosomes, fitness);
  CALCULATE_FITNESS(FITNESS_ARGV ((global CHROMOSOME_TYPE*) chromosomes) + idx, fitness + idx,
                    CHROMOSOME_SIZE, POPULATION_SIZE);
  barrier(CLK_GLOBAL_MEM_FENCE);
}
