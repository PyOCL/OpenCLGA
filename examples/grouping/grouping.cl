
float calc_linear_distance(float x1, float y1, float x2, float y2)
{
  return sqrt(pown(x2 - x1, 2) + pown(y2 - y1, 2));
}

void grouping_fitness(global __SimpleChromosome* chromosome,
                      global float* fitnesses,
                      int chromosome_size,
                      int chromosome_count,
                      global int* numOfGroups,
                      global float* pointX,
                      global float* pointY)
{
  float dist = 0.0;
  int group = numOfGroups[0];
  for (int i = 0; i < group; i++) {
    for (int j = 0; j < chromosome_size; j++) {
      for (int k = j+1; k < chromosome_size; k++) {
        // Calculate the sum of dist among all points in the same group.
        if (i == chromosome->genes[j] && i == chromosome->genes[k]) {
          dist += calc_linear_distance(pointX[j],
                                       pointY[j],
                                       pointX[k],
                                       pointY[k]);
        }
      }
    }
  }
  *fitnesses = dist;
}
