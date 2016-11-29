typedef struct {
  float data[GLOBAL_SIZE];
} TypedStruct;

__kernel void casting_test(__global const float* a_g, __global const float* b_g,
                           __global float *res_g) {

  int id = get_global_id(0);
  if (id >= GLOBAL_SIZE) {
    return;
  }
  __global TypedStruct* tsA = (__global TypedStruct*) a_g;
  __global TypedStruct* tsB = (__global TypedStruct*) b_g;
  __global TypedStruct* tsR = (__global TypedStruct*) res_g;
  tsR->data[id] = tsA->data[id] + tsB->data[id];
}
