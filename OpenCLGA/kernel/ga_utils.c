#ifndef __ga_utils__
#define __ga_utils__

#include "Noise.cl"

void print_chromosomes(global int* chromosomes, int size_of_chromosome,
                       int num_of_chromosomes, global float* fitnesses)
{
  int idx = get_global_id(0);
  if (idx > 0) {
    return;
  }
  for (int c = 0; c < num_of_chromosomes; c++) {
    int start = c * size_of_chromosome;
    printf("Chromosome[%d]/dist[%f]:", c, fitnesses[c]);
    for (int i = 0; i < size_of_chromosome; i++) {
        printf("->(%d)", chromosomes[start+i]);
    }
    printf("\n");
  }
  printf("\n");
}

void chromosome_swap(int idx, global int* chromosomes, int chromosome_size,
                     int cp, int p1)
{
  int c1 = idx * chromosome_size;
  uint temp_p = chromosomes[c1+cp];
  chromosomes[c1+cp] = chromosomes[c1+p1];
  chromosomes[c1+p1] = temp_p;
}

void calc_min_max_fitness(global float* fitnesses, int num_of_chromosomes, float* min, float* max)
{
  for (int i = 0; i < num_of_chromosomes; i++) {
    max[0] = fmax(fitnesses[i], max[0]);
    min[0] = fmin(fitnesses[i], min[0]);
  }
}

// holder - A lenght 1 array which stores the last rand value.
// Returns a random uint value.
// NOTE : Since we cannot create a real random number in kernel,
//        By passing in a random value from python, and storing the last
//        random value generated from table, we could simulate a pesudo random
//        number in kernel.
uint rand(uint* holder)
{
  uint b = ParallelRNG(holder[0]);
  uint c = ParallelRNG2(b, holder[0]);
  uint d = ParallelRNG3(c, b, holder[0]);
  holder[0] = c;
  return d;
}

// holder - A lenght 1 array which stores the last rand value.
// Returns a random uint value in the range.
uint rand_range(uint* holder, uint range)
{
  uint r = rand(holder) % range;
  return r;
}

// holder - A lenght 1 array which stores the last rand value.
// Returns a random uint value in the range except aExcluded.
uint rand_range_exclude(uint* holder, uint range, uint aExcluded)
{
  uint r = rand(holder) % range;
  while (r == aExcluded) {
    r = rand(holder) % range;
  }
  return r;
}

// holder - A lenght 1 array which stores the last rand value.
// Returns a random float value from 0.0~1.0
float rand_prob(uint* holder)
{
  uint r = rand(holder);
  float p = r / (float)UINT_MAX;
  return p;
}

// idx - global id
// holder - A lenght 1 array which stores the last rand value.
void init_rand(int idx, uint* holder)
{
  holder[0] = ParallelRNG(idx);
}


int random_choose_by_ratio(global float* ratio, uint* ra, int population)
{

  // generate a random number from between 0 and 1
  float rand_choose = rand_prob(ra);
  float accumulated = 0.0;
  int i;
  // random choose a chromosome based on probability of each chromosome.
  for (i = 0; i < population; i++) {
    accumulated += ratio[i];
    if (accumulated > rand_choose) {
      return i;
    }
  }
  return population - 1;
}

// Find min / max fitnesses among all chromosomes.
// Calculate a ratio table to identify share of each chromosome among all chromosomes.
void utils_calc_ratio(global float* fitness,
                      global float* ratio,
                      global float* best,
                      global float* worst,
                      global float* avg,
                      int idx,
                      int population)
{
  float local_min = INT_MAX;
  float local_max = 0;
#if OPTIMIZATION_FOR_MAX
  calc_min_max_fitness(fitness, population, &local_max, &local_min);
  *best = local_max;
  *worst = local_min;
#else
  calc_min_max_fitness(fitness, population, &local_min, &local_max);
  *best = local_min;
  *worst = local_max;
#endif

  float temp_worst = *worst;
  float diffTotal = 0;
  float avg_local = 0;
  int i;
  // we use total and diff to calculate the probability for each chromosome
  for (i = 0; i < population; i++) {
    diffTotal += (temp_worst - fitness[i]) * (temp_worst - fitness[i]);
    avg_local += fitness[i] / population;
  }
  // calculate probability for each one
  for (i = 0; i < population; i++) {
    ratio[i] = (temp_worst - fitness[i]) * (temp_worst - fitness[i]) / diffTotal;
  }
  *avg = avg_local;
}

#endif
