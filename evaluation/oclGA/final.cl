#define POPULATION_SIZE 1000
#define POPULATE_FUNCTION shuffler_chromosome_populate
#define CHROMOSOME_TYPE __ShufflerChromosome

#define CHROMOSOME_SIZE SHUFFLER_CHROMOSOME_GENE_SIZE
#define CROSSOVER shuffler_chromosome_crossover
#define MUTATE shuffler_chromosome_mutate
#define CALCULATE_FITNESS simple_tsp_fitness

#define SIMPLE_GENE_ELEMENTS {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19}
#define SHUFFLER_CHROMOSOME_GENE_SIZE 20
typedef struct {
  int genes[20];
} __ShufflerChromosome;

#include "simple_gene.c"
#include "shuffler_chromosome.c"


#define TSP_POINT_X {86.5870467495786, 64.2256743686222, 66.24283533521178, 77.96605553849948, 55.13160338561022, 18.594736346807995, 55.67442646112746, 81.09137769124838, 85.43404466681757, 72.20344704683913, 70.76305501476351, 81.6603684096732, 97.62153878727004, 38.77451049861009, 48.23205673926082, 53.99495303183306, 1.7596025050012676, 54.9486381209774, 94.08298357843088, 1.0111346870493976}
#define TSP_POINT_Y {20.95357182983375, 20.197845835607207, 46.15589320625547, 17.578352878428095, 2.0069515175638375, 88.17035108303234, 21.61504356180386, 17.021547576056296, 99.89358636821439, 44.670710084934676, 63.55525797935005, 60.79918537099667, 81.08363129620022, 43.24460247868392, 64.07962385984582, 21.781015754006326, 16.112851303305497, 72.56892194100492, 25.38116548288738, 27.00293001524583}

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
