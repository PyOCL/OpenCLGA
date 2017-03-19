
__kernel void casting_test(__global const float4* a_g, __global const float4* b_g,
                           __global float4 *res_g) {

  int id = get_global_id(0);
  if (id >= (GLOBAL_SIZE)) {
    return;
  }
  __global TypedStruct2* tsA = (__global TypedStruct2*) a_g;
  __global TypedStruct2* tsB = (__global TypedStruct2*) b_g;
  __global TypedStruct2* tsR = (__global TypedStruct2*) res_g;

%code_generation%
}
