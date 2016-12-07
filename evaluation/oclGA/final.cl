#define POPULATION_SIZE 100
#define POPULATE_FUNCTION shuffler_chromosome_populate
#define CHROMOSOME_TYPE __ShufflerChromosome

#define CHROMOSOME_SIZE SHUFFLER_CHROMOSOME_GENE_SIZE
#define CROSSOVER shuffler_chromosome_crossover
#define MUTATE shuffler_chromosome_mutate
#define CALCULATE_FITNESS simple_tsp_fitness

#define SIMPLE_GENE_ELEMENTS {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
#define SHUFFLER_CHROMOSOME_GENE_SIZE 10
typedef struct {
  int genes[10];
} __ShufflerChromosome;

#include "simple_gene.c"
#include "shuffler_chromosome.c"


#define TSP_POINT_X {92.6312858507014, 78.40890879298472, 97.81985488110166, 43.2704538915471, 42.808150969944045, 99.05601753181634, 81.11427894119915, 58.30951781521969, 25.586262999516585, 73.24142311595895}
#define TSP_POINT_Y {17.981894864531622, 53.86455257634712, 55.32372501169463, 7.9297526955220405, 96.38987946757774, 25.31075994720866, 21.091062181532394, 40.544497002459345, 43.04607864469172, 67.77981345248907}

float calc_linear_distance(float x1, float y1, float x2, float y2)
{
  return sqrt(pown(x2 - x1, 2) + pown(y2 - y1, 2));
}

void simple_tsp_fitness(global __ShufflerChromosome* chromosome,
                        global float* fitnesses,
                        int chromosome_size,
                        int chromosome_count)
{

  float pointsX[] = TSP_POINT_X;
  float pointsY[] = TSP_POINT_Y;

  float dist = 0.0;
  for (int i = 0; i < chromosome_size-1; i++) {
    dist += calc_linear_distance(pointsX[chromosome->genes[i + 1]],
                                  pointsY[chromosome->genes[i + 1]],
                                  pointsX[chromosome->genes[i]],
                                  pointsY[chromosome->genes[i]]);
  }
  dist += calc_linear_distance(pointsX[chromosome->genes[0]],
                                pointsY[chromosome->genes[0]],
                                pointsX[chromosome->genes[chromosome_size - 1]],
                                pointsY[chromosome->genes[chromosome_size - 1]]);
  *fitnesses = dist;
}
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
