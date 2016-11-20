#include "ga_utils.c"

void mutate(int idx, int chromosome_size, int chromosome_count,
            global int* chromosomes, float aProb_m, uint* rand_holder)
{
  for (int i = 0; i < chromosome_size; i++) {
    float prob_m =  rand_prob(rand_holder);
    if (prob_m < aProb_m) {
      uint j = rand_range_exclude(rand_holder, chromosome_size, i);
      chromosome_swap(idx, chromosomes, chromosome_size, i, j);
    }
  }
}
