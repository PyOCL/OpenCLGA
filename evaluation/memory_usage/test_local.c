
#define LM_SIZE 8192

__kernel void test(int size, global int* in, global int* out)
{
  int2 globalId = (int2)(get_global_id(0), get_global_id(1));
  int2 localId = (int2)(get_local_id(0), get_local_id(1));
  int2 groupId = (int2)(get_group_id (0), get_group_id (1));
  int2 globalSize = (int2)(get_global_size(0), get_global_size(1));
  int2 locallSize = (int2)(get_local_size(0), get_local_size(1));
  if (globalId.x + globalId.y * globalSize.x >= size) {
    return;
  }

  int gIdx = globalId.x + globalId.y * globalSize.x;
  /*
   * Device local memory size can be queired from
   import pyopencl as cl
   cl.Kernel.get_work_group_info(cl.kernel_work_group_info.LOCAL_MEM_SIZE, cl.Device)
   */

  // The local memory usage will be 4*LM_SIZE bytes.
  // You may adjust LM_SIZE to test if OUT OF RESOURCES while compiling.
  __local int lv[LM_SIZE];
  int lIdx = gIdx % LM_SIZE;
  lv[lIdx] = globalId.y + globalId.x * globalSize.y;

  /*
   * On Intel CPU, 128 bytes private memory is used for the barrier below.
   */
  // barrier(CLK_LOCAL_MEM_FENCE);
  out[gIdx] = lv[lIdx] - gIdx;
}

__kernel void test_input(int size, global int* in, global int* out, local int* lv, int lv_size)
{
  int2 globalId = (int2)(get_global_id(0), get_global_id(1));
  int2 localId = (int2)(get_local_id(0), get_local_id(1));
  int2 groupId = (int2)(get_group_id (0), get_group_id (1));
  int2 globalSize = (int2)(get_global_size(0), get_global_size(1));
  int2 locallSize = (int2)(get_local_size(0), get_local_size(1));
  if (globalId.x + globalId.y * globalSize.x >= size) {
    return;
  }

  int gIdx = globalId.x + globalId.y * globalSize.x;
  /*
   * Device local memory size can be queired from
   import pyopencl as cl
   cl.Kernel.get_work_group_info(cl.kernel_work_group_info.LOCAL_MEM_SIZE, cl.Device)
   */

  // The local memory usage will be 4*LM_SIZE bytes.
  // You may adjust LM_SIZE to test if OUT OF RESOURCES while compiling.
  int lIdx = gIdx % lv_size;
  lv[lIdx] = globalId.y + globalId.x * globalSize.y;
  if (lIdx >= 512) {
    lv[lIdx] -= 128;
  }
  /*
   * On Intel CPU, 128 bytes private memory is used for the barrier below.
   */
  // barrier(CLK_LOCAL_MEM_FENCE);
  out[gIdx] = lv[lIdx] - gIdx;
}
