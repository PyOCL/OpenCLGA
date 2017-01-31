float expansion_calc_difference(global __SimpleChromosome* chromosome,
                                int x,
                                int y) {
  float xy = 0.0 + x + y;
  float expected = pown(xy, 10);
  float calculated = 0.0;

  for (int i = 0; i < 11; i++) {
    calculated += (*chromosome).genes[i] * pown((float)x, 10 - i) * pown((float)y, i);
  }
  return fabs(expected - calculated);
}

void expansion_fitness(global __SimpleChromosome* chromosome,
                        global float* fitnesses,
                        int chromosome_size,
                        int chromosome_count)
{
  float diff = 0.0;
  for (int x = 1; x < 10; x++) {
    for (int y = 1; y < 10; y++) {
      diff += expansion_calc_difference(chromosome, x, y);
    }
  }
  // We should divide to 1,000,000 to prevent overflow of python float.
  *fitnesses = diff / 1000000;
}
