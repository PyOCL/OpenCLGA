#include "ga_utils.c"
#include "ga_mutation.c"

typedef struct {
  float x;
  float y;
} Point;

float calc_linear_distance(float x1, float y1, float x2, float y2)
{
  return sqrt(pown(x2 - x1, 2) + pown(y2 - y1, 2));
}

float calc_spherical_distance(float x1, float y1, float x2, float y2)
{
  float rad_x1 = x1 * 3.141592653589793 / 180.0;
  float rad_x2 = x2 * 3.141592653589793 / 180.0;
  float a = rad_x1 - rad_x2;
  float b = y1 * 3.141592653589793 / 180.0 - y2 * 3.141592653589793 / 180.0;
  float s = 2 * asin(sqrt(pow(sin(a/2),2)+cos(rad_x1)*cos(rad_x2)*pow(sin(b/2),2)));
  s = s * 6378.137;
  return s;
}

void calc_spherical_fitness(int idx,
                            global Point* points,
                            global int* chromosomes,
                            global float* distances,
                            int chromosome_size,
                            int chromosome_count)
{
  float dist = 0.0;
  int c_start = idx * chromosome_size;
  for (int i = 0; i < chromosome_size-1; i++) {
    dist += calc_spherical_distance(points[chromosomes[c_start + i + 1]].x,
                                    points[chromosomes[c_start + i + 1]].y,
                                    points[chromosomes[c_start + i]].x,
                                    points[chromosomes[c_start + i]].y);
  }
  dist += calc_spherical_distance(points[chromosomes[c_start]].x,
                                  points[chromosomes[c_start]].y,
                                  points[chromosomes[c_start + chromosome_size - 1]].x,
                                  points[chromosomes[c_start + chromosome_size - 1]].y);
  distances[idx] = dist;
}

void calc_linear_fitness(int idx,
                         global Point* points,
                         global int* chromosomes,
                         global float* distances,
                         int chromosome_size,
                         int chromosome_count)
{
  float dist = 0.0;
  int c_start = idx * chromosome_size;
  for (int i = 0; i < chromosome_size-1; i++) {
    dist += calc_linear_distance(points[chromosomes[c_start + i + 1]].x,
                                 points[chromosomes[c_start + i + 1]].y,
                                 points[chromosomes[c_start + i]].x,
                                 points[chromosomes[c_start + i]].y);
  }
  dist += calc_linear_distance(points[chromosomes[c_start]].x,
                               points[chromosomes[c_start]].y,
                               points[chromosomes[c_start + chromosome_size - 1]].x,
                               points[chromosomes[c_start + chromosome_size - 1]].y);
  distances[idx] = dist;
}

int find_survied_idx(uint* ra, global bool* surviors, int chromosome_count)
{
  uint s_idx = rand_range(ra, chromosome_count);
  while (!surviors[s_idx]) {
    s_idx = rand_range(ra, chromosome_count);
  }
  return s_idx;
}

void print_chrosomes(int idx, global int* chromosomes, int chromosome_size,
                    int chromosomes_count, global float* distances)
{
  if (idx != 0) {
    return;
  }
  for (int c = 0; c < chromosomes_count; c++) {
    int start = c * chromosome_size;
    printf("Chromosome[%d]/dist[%f]:", c, distances[c]);
    for (int i = 0; i < chromosome_size; i++) {
        printf("->(%d)", chromosomes[start+i]);
    }
    printf("\n");
  }
  printf("\n");
}

void reproduce(global int* chromosomes, global bool* survivors,
               int num_of_chromosomes, int size_of_chromosome,
               float prob_crossover,
               uint* ra)
{
  int idx = get_global_id(0);
  // NOTE: Only dead chromosome needs to be reproduced.
  if (survivors[idx]) {
    return;
  }

  int c_start = idx * size_of_chromosome;
  uint c1_idx = find_survied_idx(ra, survivors, num_of_chromosomes);
  int c1_start = c1_idx * size_of_chromosome;

  float prob =  rand_prob(ra);
  // printf(" >>>>> not live - idx(%d)/ c1idx(%d), prob(%f)\n", idx, c1_idx, p_v);
  if (prob <= prob_crossover) {
    for (int i = 0; i < size_of_chromosome; i++) {
      chromosomes[c_start + i] = chromosomes[c1_start + i];
    }

    uint c2_idx = find_survied_idx(ra, survivors, num_of_chromosomes);
    // do crossover here
    uint cross_point = rand_range(ra, size_of_chromosome);
    int c2_start = c2_idx * size_of_chromosome;
    for (int i = 0; i < size_of_chromosome; i++) {
      if (chromosomes[c_start + i] == chromosomes[c2_start + cross_point]) {
        // printf("  <<<<< not live idx(%d)- c2_idx(%d) / cp(%u) / i(%d) \n", idx, c2_idx, cross_point, i);
        chromosome_swap(idx, chromosomes, size_of_chromosome, cross_point, i);
        break;
      }
    }
  } else {
    for (int i = 0; i < size_of_chromosome; i++) {
      chromosomes[c_start + i] = chromosomes[c1_start + i];
    }
  }

  // NOTE: [Kilik] I don't think we need this calculation.
  // calc_linear_fitness(idx, points, chromosomes, distances, size_of_chromosome, num_of_chromosomes);
}

void update_survivors(global float* fitnesses, global float* global_best,
                      global float* global_weakest, int num_of_chromosomes,
                      global bool* survivors)
{
  int idx = get_global_id(0);
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
__kernel void tsp_one_generation(global Point* points,
                                 global int* chromosomes,
                                 global float* distances,
                                 global bool* survivors,
                                 global int* input_rand,
                                 global float* best_global,
                                 global float* weakest_global,
                                 int chromosome_size,
                                 int chromosome_count,
                                 float prob_mutate,
                                 float prob_crossover)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= chromosome_count) {
    return;
  }
  // create a private variable for each kernel to hold randome number.
  uint ra[1];
  init_rand(idx+input_rand[0], ra);

  calc_linear_fitness(idx, points, chromosomes, distances, chromosome_size, chromosome_count);
  // calc_spherical_fitness(idx, points, chromosomes, distances, chromosome_size, chromosome_count);
  // Barrier for the calculation of all chromosomes fitness.
  barrier(CLK_GLOBAL_MEM_FENCE);
  // printf("[FirstRound] idx(%d), fit(%f), rand(%u)\n", idx, distances[idx], rand(ra));

  update_survivors(distances, best_global, weakest_global, chromosome_count, survivors);
  // Barrier for survivor list.
  barrier(CLK_GLOBAL_MEM_FENCE);

  reproduce(chromosomes, survivors, chromosome_count, chromosome_size,
            prob_crossover, ra);
  // Barrier for mutation, we need to make sure to reproduction for all chromosomes
  // is done to prevent mutation with weak chromosomes.
  barrier(CLK_GLOBAL_MEM_FENCE);
  // print_chrosomes(idx, chromosomes, chromosome_size, chromosome_count, distances);

  mutate(idx, chromosome_size, chromosome_count, chromosomes,
         prob_mutate, ra);
  // // Barrier for next round.
  // barrier(CLK_GLOBAL_MEM_FENCE);
  // print_chrosomes(idx, chromosomes, chromosome_size, chromosome_count, distances);
}
