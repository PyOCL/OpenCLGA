
#include "ga_utils.cl"

float calc_linear_distance(float x1, float y1, float x2, float y2)
{
  return sqrt(pown(x2 - x1, 2) + pown(y2 - y1, 2));
}

float calc_cost(local int* solution, global float* xy)
{
  float cost = 0.0;
  int next_i, x, y, nx, ny;
  for (int i = 0; i < SOLUTION_SIZE; i++) {
    next_i = (i+1) % SOLUTION_SIZE;
    x = xy[solution[i]*2];
    y = xy[solution[i]*2+1];
    nx = xy[solution[next_i]*2];
    ny = xy[solution[next_i]*2+1];
    cost += calc_linear_distance(x, y, nx, ny);
  }
  return cost;
}

float acceptance_probability(float old_cost, float new_cost, float temperature)
{
  if (new_cost < old_cost) {
    return 1.0;
  }
  return exp((old_cost - new_cost) / temperature);
}

void find_neighbor(uint* rand_holder, local int* ori_solution,
                   local int* neighbor_solution)
{
  int rndIdxA, rndIdxB;
  rndIdxA = rand_range(rand_holder, SOLUTION_SIZE);
  rndIdxB = rand_range(rand_holder, SOLUTION_SIZE);
  while (rndIdxA == rndIdxB) {
    rndIdxB = rand_range(rand_holder, SOLUTION_SIZE);
  }
  neighbor_solution[rndIdxA] = ori_solution[rndIdxB];
  neighbor_solution[rndIdxB] = ori_solution[rndIdxA];
}

__kernel void ocl_sa_populate_solutions(int iterations,
                                        float temperature,
                                        float terminate_temperature,
                                        float alpha,
                                        global int* solutions,
                                        global uint* rand_holder,
                                        global float* xy,
                                        global float* costs)
{
  int idx = get_global_id(0);

  if (idx >= NUM_OF_SOLUTION) {
    return;
  }
  // create a private variable for each kernel to hold randome number.
  uint ra[1];
  init_rand(rand_holder[idx], ra);

  int elements[] = ELEMENT_SPACE;
  int rndIdx;

  __local int target_solution[SOLUTION_SIZE];
  __local int neighbor_solution[SOLUTION_SIZE];

  for (int i = 0; i < SOLUTION_SIZE - 1; i++) {
    rndIdx = rand_range(ra, (SOLUTION_SIZE - i - 1));
    target_solution[i] = elements[rndIdx];
    elements[rndIdx] = elements[SOLUTION_SIZE - i - 1];
  }
  target_solution[SOLUTION_SIZE - 1] = elements[0];

  int iter;
  float ap;
  float target_cost, neighbor_cost;
  float temp_temperature = temperature;

  target_cost = calc_cost(target_solution, xy);
  while (temp_temperature > terminate_temperature) {
    iter = 1;
    while (iter <= iterations) {
      for (int i = 0; i < SOLUTION_SIZE; i++) {
        neighbor_solution[i] = target_solution[i];
      }
      find_neighbor(ra, target_solution, neighbor_solution);
      neighbor_cost = calc_cost(neighbor_solution, xy);

      ap = acceptance_probability(target_cost, neighbor_cost, temp_temperature);
      if (ap > rand_prob(ra)) {
        for (int i = 0; i < SOLUTION_SIZE; i++) {
          target_solution[i] = neighbor_solution[i];
          target_cost = neighbor_cost;
        }
      }
      iter += 1;
    }
    temp_temperature = temp_temperature * alpha;
  }

  global int* result_solution = solutions + idx * SOLUTION_SIZE;
  for (int i = 0; i < SOLUTION_SIZE; i++) {
    result_solution[i] = target_solution[i];
  }
  costs[idx] = target_cost;
}
