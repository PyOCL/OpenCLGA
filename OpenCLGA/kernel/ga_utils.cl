#ifndef __ga_utils__
#define __ga_utils__

#include "Noise.cl"

/**
 * prints the value of chromosomes. We can also use this function to print a
 * single chromome with 1 value of num_of_chromosomes.
 * @param *chromosomes (global) the reference of chromosomes array
 * @param size_of_chromosome the size of a single chromesome
 * @param num_of_chromosomes the number of chromosomes in this array.
 * @param *fitnesses (global) the fitness array of all chromosomes. The size of
 *        this array is num_of_chromosomes.
 */
void print_chromosomes(global int* chromosomes, int size_of_chromosome,
                       int num_of_chromosomes, global float* fitnesses)
{
  int idx = get_global_id(0);
  if (idx > 0) {
    // We use this function to dump all of chromosomes. In most of the cases,
    // we shouldn't let all threads to print result because it may give us too
    // many information. So, the first thread is the only one can dump infos.
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

/**
 * rand generates a random number between 0 to max value of uint.
 * NOTE : Since we cannot create a real random number in kernel,
 *        By passing in a random value from python, and storing the last
 *        random value generated from table, we could simulate a pesudo random
 *        number in kernel.
 * @param *holder a pointer of uint for storing the last rand value.
 * @return a random uint value.
 */
uint rand(uint* holder)
{
  uint b = ParallelRNG(holder[0]);
  uint c = ParallelRNG2(b, holder[0]);
  uint d = ParallelRNG3(c, b, holder[0]);
  holder[0] = c;
  return d;
}

/**
 * rand_range generates a random number between 0 < return_vlue < range.
 * @param *holder a pointer of uint for storing the last rand value.
 * @param range the max value of random number.
 * @return a random uint value in the range.
 */
uint rand_range(uint* holder, uint range)
{
  uint r = rand(holder) % range;
  return r;
}

/**
 * rand_range_exclude generates a random number between 0 < return_vlue < range.
 * But the value aExcluded is excluded.
 * @param *holder a pointer of uint for storing the last rand value.
 * @param range the max value of random number.
 * @param aExclude the excluded value
 * @return a random uint value in the range except aExcluded.
 */
uint rand_range_exclude(uint* holder, uint range, uint aExcluded)
{
  uint r = rand(holder) % (range - 1);
  return r == aExcluded ? range - 1 : r;
}

/**
 * rand_prob generates a random number between 0 < return_vlue < 1 in float.
 * @param *holder a pointer of uint for storing the last rand value.
 * @return a random float value.
 */
float rand_prob(uint* holder)
{
  uint r = rand(holder);
  float p = r / (float)UINT_MAX;
  return p;
}

/**
 * initialze the random seed.
 * @param seed the reandom seed.
 * @param *holder a pointer of uint for storing the last rand value.
 */
void init_rand(int seed, uint* holder)
{
  holder[0] = ParallelRNG(seed);
}

/**
 * random choose a chromosome based on the ratio. For GA, we need to choose a
 * chromosome for crossover based on fitnesses. If a chromosome with better
 * fitness, the probability is higher. The ratio is an array with population in
 * size. The value in ratio array is the uniform[0, 1] distribution value. The
 * accumulated value of the whole array is 1.
 * @param *ratio (global) the probability array for each chromosomes.
 * @param *holder a pointer of uint for storing the last rand value.
 * @param num_of_chromosomes the size of ratio.
 */
int random_choose_by_ratio(global float* ratio, uint* holder,
                           int num_of_chromosomes)
{

  // generate a random number from between 0 and 1
  float rand_choose = rand_prob(holder);
  float accumulated = 0.0;
  int i;
  // random choose a chromosome based on probability of each chromosome.
  for (i = 0; i < num_of_chromosomes; i++) {
    accumulated += ratio[i];
    if (accumulated > rand_choose) {
      return i;
    }
  }
  return num_of_chromosomes - 1;
}

/**
 * calc_min_max_fitness find the max and min value among all fitness values.
 * @param *fitnesses (global) the fitness value array of all chromosomes
 * @param num_of_chromosomes the number of chromosomes
 * @param *min (out) for returing the min fitness value
 * @param *max (out) for returning the max fitness value
 */
void calc_min_max_fitness(global float* fitnesses, int num_of_chromosomes,
                          float* min, float* max)
{
  for (int i = 0; i < num_of_chromosomes; i++) {
    max[0] = fmax(fitnesses[i], max[0]);
    min[0] = fmin(fitnesses[i], min[0]);
  }
}

/**
 * utils_calc_ratio find the best, worst, avg fitnesses among all chromosomes.
 * It also calculates the probability for each chromosomes based on their
 * fitness value. The best and worst definition is based on the initial options
 * of OpenCLGA.
 * @param *fitness (global) the fitness value array of all chromosomes
 * @param *ratio (global, out) the probability array of each chromosomes
 * @param num_of_chromosomes the number of chromosomes.
 */
void utils_calc_ratio(global float* fitness,
                      global float* ratio,
                      int num_of_chromosomes)
{
  float local_min = INT_MAX;
  float local_max = 0;
  // OPTIMIZATION_FOR_MAX is set at ocl_ga.py
  float best;
  float worst;
#if OPTIMIZATION_FOR_MAX
  calc_min_max_fitness(fitness, num_of_chromosomes, &local_max, &local_min);
  best = local_max;
  worst = local_min;
#else
  calc_min_max_fitness(fitness, num_of_chromosomes, &local_min, &local_max);
  best = local_min;
  worst = local_max;
#endif

  float temp_worst = worst;
  float diffTotal = 0;
  int i;
  // we use total and diff to calculate the probability for each chromosome
  for (i = 0; i < num_of_chromosomes; i++) {
    // to have a significant different between better and worst, we use square
    // of diff to calculate the probability.
    diffTotal += (temp_worst - fitness[i]) * (temp_worst - fitness[i]);
  }
  // calculate probability for each one
  for (i = 0; i < num_of_chromosomes; i++) {
    ratio[i] = (temp_worst - fitness[i]) * (temp_worst - fitness[i]) /
               diffTotal;
  }
}

#endif
