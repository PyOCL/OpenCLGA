#include "tsp_utils.c"

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

void calc_fitness(int idx,
                  global Point* points,
                  global int* chromosomes,
                  global float* distances,
                  int chromosome_size,
                  int chromosome_count)
{
  float dist = 0.0;
  int c_start = idx * chromosome_size;
  for (int i = 0; i < chromosome_size-1; i++) {
    dist += calc_linear_distance(points[chromosomes[c_start + i + 1]].x, points[chromosomes[c_start + i + 1]].y,
                                 points[chromosomes[c_start + i]].x, points[chromosomes[c_start + i]].y);
  //  dist += calc_spherical_distance(points[chromosomes[c_start + i + 1]].x, points[chromosomes[c_start + i + 1]].y,
  //                                  points[chromosomes[c_start + i]].x, points[chromosomes[c_start + i]].y);
  }
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

void print_chrosome(int idx, global int* chromosomes, int chromosome_size)
{
  printf("idx(%d) - ", idx);
  int start = idx * chromosome_size;
  for (int i = 0; i < chromosome_size; i++) {
      printf("idx(%d)-%d,", idx, chromosomes[start+i]);
  }
  printf("\n");
}

void chromosome_swap(int idx, global int* chromosomes, int chromosome_size,
                     int c1, int cp, int p1)
{
  // print_chrosome(idx, chromosomes, chromosome_size);
  // printf("idx(%d) before - cp(%d), p1(%d) \n", idx, cp, p1);
  // for (int i = 0; i < chromosome_size; i++) {
  //     printf("idx(%d) - %d \n", idx, chromosomes[c1+i]);
  // }
  // printf(" >>>>>>>>>>>>>>>>>>>> \n");
  uint temp = chromosomes[c1+cp];
  chromosomes[c1+cp] = chromosomes[c1+p1];
  if (p1 == 0) {
    chromosomes[c1 + chromosome_size-1] = temp;
  }
  chromosomes[c1+p1] = temp;
  // printf("idx(%d) after ..................... \n", idx);
  // for (int i = 0; i < chromosome_size; i++) {
  //     printf("idx(%d) - %d \n", idx, chromosomes[c1+i]);
  // }
}

void reproduce(int idx, int chromosome_size, int chromosome_count,
               global int* chromosomes, global bool* survivors, float p_c,
               uint* ra)
{
  bool ilive = survivors[idx];

  if (!ilive) {
    int c_start = idx * chromosome_size;
    uint c1_idx = find_survied_idx(ra, survivors, chromosome_count);
    float p_v =  rand_prob(ra);
    // printf(" >>>>> not live - idx(%d)/ c1idx(%d), p_v(%f)\n", idx, c1_idx, p_v);
    if (p_v < p_c) {
      uint c2_idx = find_survied_idx(ra, survivors, chromosome_count);
      // do crossover here
      uint cross_point = rand_range(ra, chromosome_size-1);
      int c1_start = c1_idx * chromosome_size;
      int c2_start = c2_idx * chromosome_size;
      // printf(" >>>>> not live idx(%d)- c1_idx(%d) / c2_idx(%d) / cp(%u) \n", idx, c1_idx, c2_idx, cross_point);
      for (int i = 0; i < chromosome_size-1; i++) {
        if (chromosomes[c1_start + i] == chromosomes[c2_start + cross_point]) {
          chromosome_swap(idx, chromosomes, chromosome_size,
                          c1_start, cross_point, i);
          break;
        }
      }
    }
    int c1_start = c1_idx * chromosome_size;
    for (int i = 0; i < chromosome_size; i++) {
      chromosomes[c_start + i] = chromosomes[c1_start + i];
    }
  }
}

void mutate()
{

}

void calc_min_max(float* min, float* max, global float* distances, int chromosome_count)
{
  for (int i = 0; i < chromosome_count; i++) {
    if (distances[i] > max[0]) {
      max[0] = distances[i];
    }
    if (distances[i] < min[0]) {
      min[0] = distances[i];
    }
  }
}

__kernel void tsp_one_generation(global Point* points,
                                 global int* chromosomes,
                                 global float* distances,
                                 global bool* survivors,
                                 global int* input_rand,
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

  calc_fitness(idx, points, chromosomes, distances, chromosome_size, chromosome_count);
  // Barrier for the calculation of all chromosomes fitness.
  barrier(CLK_GLOBAL_MEM_FENCE);
  printf("[FirstRound] idx(%d), fit(%f), rand(%u)\n", idx, distances[idx], rand(ra));

  float min[1];
  float max[1];
  min[0] = INT_MAX;
  max[0] = 0.0;
  calc_min_max(min, max, distances, chromosome_count);

  // Calculate surviors indice.
  float threshold = min[0] + (max[0] - min[0]) / 2;
  for (int i = 0; i < chromosome_count; i++) {
    int live = false;
    if (distances[i] <= threshold) {
      live = true;
    }
    survivors[i] = live;
  }

  reproduce(idx, chromosome_size, chromosome_count, chromosomes, survivors,
            prob_crossover, ra);

  calc_fitness(idx, points, chromosomes, distances, chromosome_size, chromosome_count);
  // Barrier for the calculation of all chromosomes fitness.
  printf("[AfterReproduce&Crossover] idx(%d), fit(%f) \n", idx, distances[idx]);
  // TBD.
}
