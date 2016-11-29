import pyopencl as cl
import numpy as np

def run(vector):
    ctx = cl.create_some_context()
    queue = cl.CommandQueue(ctx, properties=cl.command_queue_properties.PROFILING_ENABLE)
    f = open("casting_vector.c" if vector else "casting.c", 'r')
    fstr = "".join(f.readlines())
    f.close()

    data_size = 100;
    global_size = int(data_size / 4) if vector else data_size

    if vector:
        struct = "typedef struct {\n"
        code = "  switch(id) {\n"
        codeTemp = "    case {0}:\n      tsR->data{0} = tsA->data{0} + tsB->data{0};\n    break;\n"
        for i in range(global_size):
            struct += "  float4 data" + str(i) + ";\n"
            code += codeTemp.format(i)
        struct += "} TypedStruct2;\n"
        code += "  }\n"
        fstr = fstr.replace("%code_generation%", code);
        fstr = "#define GLOBAL_SIZE " + str(global_size) + "\n" + struct + fstr
    else:
        fstr = "#define GLOBAL_SIZE " + str(global_size) + "\n" + fstr;

    print("=" * 50)
    print(fstr)
    print("-" * 50)

    a_np = np.random.rand(data_size).astype(np.float32)
    b_np = np.random.rand(data_size).astype(np.float32)

    mf = cl.mem_flags
    a_g = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=a_np)
    b_g = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=b_np)

    res_g = cl.Buffer(ctx, mf.WRITE_ONLY, a_np.nbytes)

    prg = cl.Program(ctx, fstr).build();
    exec_evt = prg.casting_test(queue, (global_size,), None, a_g, b_g, res_g)
    exec_evt.wait()

    res_np = np.empty_like(a_np)
    cl.enqueue_copy(queue, res_np, res_g).wait()
    print(res_np)

    elapsed = 1e-9 * (exec_evt.profile.end - exec_evt.profile.start)
    print("Vector: {0} => Execution time of test: {1}s".format(vector, elapsed))

if __name__ == '__main__':
    run(False)
    run(True)
