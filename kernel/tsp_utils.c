#include "Noise.cl"

// holder - A lenght 1 array which stores the last rand value.
// Returns a random uint value.
uint rand(uint* holder)
{
  uint b = ParallelRNG(holder[0]);
  holder[0] = b;
  return b;
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
