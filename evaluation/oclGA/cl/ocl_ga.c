#include "ga_utils.c"

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
