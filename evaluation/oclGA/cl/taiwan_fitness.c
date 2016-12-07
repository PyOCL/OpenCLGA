
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

void taiwan_fitness(global __ShufflerChromosome* chromosome,
                    global float* fitnesses,
                     int chromosome_size,
                     int chromosome_count)
{

  float pointsX[] = TAIWAN_POINT_X;
  float pointsY[] = TAIWAN_POINT_Y;

  float dist = 0.0;
  for (int i = 0; i < chromosome_size-1; i++) {
    dist += calc_spherical_distance(pointsX[chromosome->genes[i + 1]],
                                    pointsY[chromosome->genes[i + 1]],
                                    pointsX[chromosome->genes[i]],
                                    pointsY[chromosome->genes[i]]);
  }
  dist += calc_spherical_distance(pointsX[chromosome->genes[0]],
                                  pointsY[chromosome->genes[0]],
                                  pointsX[chromosome->genes[chromosome_size - 1]],
                                  pointsY[chromosome->genes[chromosome_size - 1]]);
  *fitnesses = dist;
}
