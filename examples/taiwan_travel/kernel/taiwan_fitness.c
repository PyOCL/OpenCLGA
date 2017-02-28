
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

float taiwan_calc_fitness(global __ShufflerChromosome* chromosome, int chromosome_size)
{
  float pointsX[] = TAIWAN_POINT_X;
  float pointsY[] = TAIWAN_POINT_Y;

  float dist = 0.0;
  for (int i = 0; i < chromosome_size - 1; i++) {
    dist += calc_spherical_distance(pointsX[chromosome->genes[i + 1]],
                                    pointsY[chromosome->genes[i + 1]],
                                    pointsX[chromosome->genes[i]],
                                    pointsY[chromosome->genes[i]]);
  }
  return dist + calc_spherical_distance(pointsX[chromosome->genes[0]],
                                        pointsY[chromosome->genes[0]],
                                        pointsX[chromosome->genes[chromosome_size - 1]],
                                        pointsY[chromosome->genes[chromosome_size - 1]]);
}

void taiwan_fitness(global __ShufflerChromosome* chromosome,
                    global float* fitnesses,
                     int chromosome_size,
                     int chromosome_count)
{
  *fitnesses = taiwan_calc_fitness(chromosome, chromosome_size);
}

void taiwan_fitness_swap(global __ShufflerChromosome* chromosome, int cp, int p1)
{
  int temp_p = chromosome->genes[cp];
  chromosome->genes[cp] = chromosome->genes[p1];
  chromosome->genes[p1] = temp_p;
}

int improving_only_mutation_helper(global int* c,
                                   int idx,
                                   int chromosome_size)
{
  global __ShufflerChromosome* chromosome = (global __ShufflerChromosome*) c;
  // We will search the one whose distance is shorter than original one
  float pointsX[] = TAIWAN_POINT_X;
  float pointsY[] = TAIWAN_POINT_Y;

  int best_index = idx;
  float shortest = taiwan_calc_fitness(chromosome, chromosome_size);
  float current;

  for (int i = 0; i < chromosome_size - 1; i++) {
    if (i == idx) {
      continue;
    }
    taiwan_fitness_swap(chromosome, i, idx);
    current = taiwan_calc_fitness(chromosome, chromosome_size);
    taiwan_fitness_swap(chromosome, i, idx);
    if (current < shortest) {
      shortest = current;
      best_index = i;
    }
  }
  return best_index;
}
