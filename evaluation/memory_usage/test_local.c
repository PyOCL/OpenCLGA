
__kernel void test(int size, global int* in, global int* out)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding

  if (idx >= size) {
    return;
  }

  __local int bb[1];
  bb[idx%1] = idx;
  barrier(CLK_LOCAL_MEM_FENCE);

  out[idx] = bb[idx];
}
