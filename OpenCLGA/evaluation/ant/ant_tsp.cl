#include "ga_utils.cl"

/* ======================== codes for preparing execution =========================== */

__kernel void ant_tsp_calculate_distances(global float* x, global float* y, global float* distances)
{
  int global_p = get_global_id(0);
  int global_q = get_global_id(1);

  float2 p = (float2)(x[global_p], y[global_p]);
  float2 q = (float2)(x[global_q], y[global_q]);
  distances[global_p * NODE_COUNT + global_q] = distance(p, q);
}


/* ======================== codes for ant going out =========================== */

bool ant_tsp_in_visited_nodes(global int* ant_visited_nodes, int last_index, int node_id) {
  int i = 0;
  for (; i <= last_index; i++) {
    if (ant_visited_nodes[i] == node_id) {
      return true;
    }
  }
  return false;
}

void ant_tsp_calculate_path_probabilities(global int* ant_visited_nodes,
                                          global float* tmp_path_probabilities,
                                          global float* tmp_pheromones,
                                          global float* path_pheromones,
                                          global float* path_distances,
                                          int last_index)
{
  float total = 0.0;
  int current_node = ant_visited_nodes[last_index];
  int i;

  for (i = 0; i < NODE_COUNT; i++) {
    if (current_node == i) {
      tmp_path_probabilities[i] = 0;
      tmp_pheromones[i] = 0;
    } else if (ant_tsp_in_visited_nodes(ant_visited_nodes, last_index, i)) {
      tmp_path_probabilities[i] = 0;
      tmp_pheromones[i] = 0;
    } else {
      tmp_pheromones[i] = pow(path_pheromones[current_node * NODE_COUNT + i], (float) ALPHA) *
                          pow(1 / path_distances[current_node * NODE_COUNT + i], (float) BETA);
      total += tmp_pheromones[i];
    }
  }

  for (i = 0; i < NODE_COUNT; i++) {
    if (tmp_pheromones[i] > 0.00001) {
      tmp_path_probabilities[i] = tmp_pheromones[i] / total;
    }
  }
}

int ant_tsp_random_choose(global float* tmp_path_probabilities, uint* rand_holder)
{
  return random_choose_by_ratio(tmp_path_probabilities, rand_holder, NODE_COUNT);
}

float ant_tsp_calculate_fitness(global int* ant_visited_nodes, global float* path_distances) {
  float fitness = 0.0;
  int i = 0;
  int start, end;
  for (; i < NODE_COUNT; i++) {
    start = ant_visited_nodes[i];
    if (i < NODE_COUNT - 1) {
      end = ant_visited_nodes[i + 1];
    } else {
      end = ant_visited_nodes[0];
    }
    fitness += path_distances[start * NODE_COUNT + end];
  }
  return fitness;
}

// A kernel work item is an ant
__kernel void ant_tsp_run_ant(global int* ant_visited_nodes,
                              global float* tmp_path_probabilities,
                              global float* tmp_pheromones,
                              global float* path_pheromones,
                              global float* path_distances,
                              global float* ant_fitnesses,
                              global uint* rand_input)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= ANT_COUNT) {
    return;
  }
  // init random numbers.
  uint ra[1];
  init_rand(rand_input[idx], ra);

  int next_index = 1;

  // The first position of visited_node is not 0. We should move it.
  global int* my_tmp_visited_nodes = ant_visited_nodes + idx * NODE_COUNT;
  global float* my_tmp_path_probabilities = tmp_path_probabilities + idx * NODE_COUNT;
  global float* my_tmp_pheromones = tmp_pheromones + idx * NODE_COUNT;
  // choose the first node randomly
  my_tmp_visited_nodes[0] = rand_range(ra, NODE_COUNT);
  // go all nodes
  for (; next_index < NODE_COUNT; next_index++) {
    ant_tsp_calculate_path_probabilities(my_tmp_visited_nodes,
                                         my_tmp_path_probabilities,
                                         my_tmp_pheromones,
                                         path_pheromones,
                                         path_distances,
                                         next_index - 1);
    my_tmp_visited_nodes[next_index] = ant_tsp_random_choose(my_tmp_path_probabilities, ra);
  }
  // calculate fitness
  ant_fitnesses[idx] = ant_tsp_calculate_fitness(my_tmp_visited_nodes, path_distances);
}

/* ======================== codes for updating pheromone =========================== */

/**
 * kernel design: each path has its owned kernel
 **/
__kernel void ant_tsp_evaporate_pheromones(global float* path_pheromones)
{
  int idx = get_global_id(0);
  path_pheromones[idx] = (1 - EVAPORATION) * path_pheromones[idx] + 1;
}

/*
 * Pheromones is a two dimensional array:
 *        from
 *    1 2 3 4 5 6
 *    -----------------------
 * t 1|
 * o 2|
 *   3|
 *
 * Since from and to can be swapped in TSP case, we have to update both side, (1, 2) and (2, 1), if
 * an ant goes through (1, 2).
 *
 * kernel design: each path has its owned kernel
 */
__kernel void ant_tsp_update_pheromones(global int* ant_visited_nodes,
                                        global float* ant_fitnesses,
                                        global float* path_pheromones)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= NODE_COUNT * NODE_COUNT) {
    return;
  }

  int ant_index, node_index, ant_start, ant_end;
  int start = idx / NODE_COUNT;
  int end = idx % NODE_COUNT;
  float bonus;

  for (ant_index = 0; ant_index < ANT_COUNT; ant_index++) {
    bonus = Q / ant_fitnesses[ant_index];
    for (node_index = 0; node_index < NODE_COUNT; node_index++) {
      if (node_index < NODE_COUNT - 1) {
        ant_start = ant_visited_nodes[ant_index * NODE_COUNT + node_index];
        ant_end = ant_visited_nodes[ant_index * NODE_COUNT + node_index + 1];
      } else {
        ant_start = ant_visited_nodes[ant_index * NODE_COUNT + node_index];
        ant_end = ant_visited_nodes[ant_index * NODE_COUNT];
      }
      if ((ant_start == start && ant_end == end) || (ant_start == end && ant_end == start)) {
        path_pheromones[idx] += bonus;
      }
    }
  }
}
