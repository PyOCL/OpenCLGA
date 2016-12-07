
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
