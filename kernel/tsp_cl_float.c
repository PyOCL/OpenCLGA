
typedef struct {
  float x;
  float y;
} Point;

float calc_linear_distance(float x1, float y1, float x2, float y2)
{
  return sqrt(pown(x2 - x1, 2) + pown(y2 - y1, 2));
}

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
    // dist += calc_linear_distance(points[chromosomes[c_start + i + 1]].x, points[chromosomes[c_start + i + 1]].y,
    //                              points[chromosomes[c_start + i]].x, points[chromosomes[c_start + i]].y);
   dist += calc_spherical_distance(points[chromosomes[c_start + i + 1]].x, points[chromosomes[c_start + i + 1]].y,
                                   points[chromosomes[c_start + i]].x, points[chromosomes[c_start + i]].y);

  }

  distances[idx] = dist;
}
