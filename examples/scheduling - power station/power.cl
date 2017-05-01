
void generate_powers_type1(int* quarters, int value, int power) {
  // for type 1 power station, it uses 2 quarters for maintainence.
  // no power generates if it is at quarter 1
  quarters[0] += (value == 0 ? 0 : power);
  // no power generates if it is at quarter 1 or quarter 2
  quarters[1] += (value == 0 || value== 1 ? power : 0);
  // no power generates if it is at quarter 2 or quarter 3
  quarters[2] += (value == 1 || value== 2 ? 0 : power);
  // no power generates if it is at quarter 3
  quarters[3] += (value == 2 ? 0 : power);
}

void generate_powers_type2(int* quarters, int value, int power) {
  // for type 2 power station, it uses 1 quarters for maintainence.
  // no power generates if it is at quarter 1
  quarters[0] += (value == 0 ? 0 : power);
  // no power generates if it is at quarter 2
  quarters[1] += (value == 1 ? 0 : power);
  // no power generates if it is at quarter 3
  quarters[2] += (value == 2 ? 0 : power);
  // no power generates if it is at quarter 4
  quarters[3] += (value == 3 ? 0 : power);
}

void power_station_fitness(global __SimpleChromosome* chromosome,
                           global float* fitnesses,
                           int chromosome_size,
                           int chromosome_count)
{

  int CAPACITIES[] = {20, 15, 34, 50, 15, 15, 10};
  int LOADS[] = {-80, -90, -65, -70};

  generate_powers_type1(LOADS, chromosome->genes[0], CAPACITIES[0]);
  generate_powers_type1(LOADS, chromosome->genes[1], CAPACITIES[1]);
  generate_powers_type2(LOADS, chromosome->genes[2], CAPACITIES[2]);
  generate_powers_type2(LOADS, chromosome->genes[3], CAPACITIES[3]);
  generate_powers_type2(LOADS, chromosome->genes[4], CAPACITIES[4]);
  generate_powers_type2(LOADS, chromosome->genes[5], CAPACITIES[5]);
  generate_powers_type2(LOADS, chromosome->genes[6], CAPACITIES[6]);

  *fitnesses = LOADS[0];

  if (LOADS[1] < *fitnesses) {
    *fitnesses = LOADS[1];
  }

  if (LOADS[2] < *fitnesses) {
    *fitnesses = LOADS[2];
  }

  if (LOADS[3] < *fitnesses) {
    *fitnesses = LOADS[3];
  }

  if (*fitnesses < 0) {
    *fitnesses = 0;
  }
}
