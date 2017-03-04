#!/usr/bin/python3

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import utils
import numpy
import pyopencl as cl


def get_context():
    contexts = []
    platforms = cl.get_platforms()
    for platform in platforms:
        devices = platform.get_devices()
        for device in devices:
            try:
                context = cl.Context(devices=[device])
                contexts.append(context)
            except:
                print("Can NOT create context from P(%s)-D(%s)"%(platform, device))
                continue
    return contexts[0] if len(contexts) > 0 else None

def build_program(ctx, filename):
    prog = None
    try:
        f = open(filename, "r")
        fstr = "".join(f.readlines())
        f.close()
        # -Werror : Make all warnings into errors.
        # https://www.khronos.org/registry/OpenCL/sdk/2.0/docs/man/xhtml/clBuildProgram.html
        prog = cl.Program(ctx, fstr).build(options=['-Werror'], cache_dir=None);
    except:
        import traceback
        traceback.print_exc()
    return prog

def create_queue(ctx):
    return cl.CommandQueue(ctx)

def create_bytearray(ctx, size):
    mf = cl.mem_flags
    py_buffer = numpy.zeros(size, dtype=numpy.int32)
    cl_buffer = cl.Buffer(ctx,
                          mf.READ_WRITE | mf.COPY_HOST_PTR,
                          hostbuf=py_buffer)
    return py_buffer, cl_buffer

if __name__ == "__main__":
    ctx = get_context()
    prog = build_program(ctx, "test_private.c")
    if ctx and prog:
        utils.calculate_estimated_kernel_usage(prog, ctx, ["private_add"])
    else:
        print("Nothing is calculated !")

    queue = create_queue(ctx)

    size = 1024
    py_in, dev_in = create_bytearray(ctx, size)
    py_out, dev_out = create_bytearray(ctx, size)
    g_wi_size = (size,)
    l_wi_size = (1,)

    prog.private_add(queue, g_wi_size, l_wi_size, numpy.int32(size),
                     dev_in, dev_out).wait()

    cl.enqueue_read_buffer(queue, dev_out, py_out)
    print(py_out)
