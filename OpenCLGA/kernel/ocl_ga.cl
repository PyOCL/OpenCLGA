#include "ga_utils.cl"

/**
 * ocl_ga_calculate_fitness is a wrapper function to call specified fitness
 * function. To simplify the implementation of fitness calcuation, we handles
 * the multi-threading part and let implementor write the core calculation.
 * Note: this is a kernel function and will be called by python.
 *
 * @param *chromosomes (global) the chromosomes array
 * @param *fitness (global) the fitness array for each chromosomes.
 * @param FITNESS_ARGS the fitness arguments from ocl_ga options.
 */
__kernel void ocl_ga_calculate_fitness(global int* chromosomes,
                                       global float* fitness FITNESS_ARGS)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= POPULATION_SIZE) {
    return;
  }
  // calls the fitness function specified by user and gives the chromosome for
  // current thread.
  CALCULATE_FITNESS(((global CHROMOSOME_TYPE*) chromosomes) + idx,
                    fitness + idx,
                    CHROMOSOME_SIZE, POPULATION_SIZE FITNESS_ARGV);
}
