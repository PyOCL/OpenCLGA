
typedef struct {
  float x;
  float y;
} Point;

__kernel  void tsp_fitness(global Point* points,
                           global int* chromosomes,
                           global float* distances,
                           int chromosome_size,
                           int chromosome_count)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding
  if (idx >= chromosome_count) {
    return;
  }

  float dist = 0.0;
  int c_start = idx * chromosome_size;
  for (int i = 0; i < chromosome_size; i++) {
    dist += sqrt(pown(points[chromosomes[c_start + i + 1]].x - points[chromosomes[c_start + i]].x, 2) +
                 pown(points[chromosomes[c_start + i + 1]].y - points[chromosomes[c_start + i]].y, 2));
  }

  distances[idx] = dist;
}
