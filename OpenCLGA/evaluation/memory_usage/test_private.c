
int calcutate(int index)
{
  int a = (index * 32) & 128;
  return a;
}

#define PM_SIZE 10240 + 4096 + 200

__kernel void test(int size, global int* in, global int* out)
{
  int idx = get_global_id(0);
  // out of bound kernel task for padding

  if (idx >= size) {
    return;
  }

  /*
   On Intel CPU, the private memroy limitation is 64 KB.
   */
  int ga[PM_SIZE] = {1};

  /*
   On Intel CPU, private memory will be used more efficient if the barrier below is used.
   That is, we can create larger ga.
   */
  // barrier(CLK_LOCAL_MEM_FENCE);

  out[idx] = ga[idx%PM_SIZE];
}
