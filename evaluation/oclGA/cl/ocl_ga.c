#include "ga_utils.c"

// Populate the first generation of chromosomes.
__kernel void ocl_ga_populate(global int* chromosomes,
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
  POPULATE_FUNCTION(((global CHROMOSOME_TYPE*) chromosomes) + idx, ra);
  input_rand[idx] = ra[0];
}

__kernel void ocl_ga_calculate_fitness(global int* chromosomes,
                                       global float* fitness FITNESS_ARGS)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }
  CALCULATE_FITNESS(((global CHROMOSOME_TYPE*) chromosomes) + idx, fitness + idx,
                    CHROMOSOME_SIZE, POPULATION_SIZE FITNESS_ARGV);
}
