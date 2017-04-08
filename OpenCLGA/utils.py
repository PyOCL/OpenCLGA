#!/usr/bin/python3
import random
from math import pi, sqrt, asin, cos, sin, pow

def get_local_IP():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 1))
    ip = s.getsockname()[0]
    s.close()
    return ip

def get_testing_params():
    return 20, 200, 5000

def init_testing_rand_seed():
    random.seed(119)

def calc_linear_distance(x1, y1, x2, y2):
    return sqrt((x2 - x1)**2 + (y2 - y1)**2)

def calc_spherical_distance(x1, y1, x2, y2):
    def rad(deg):
        return deg * pi / 180.0
    rad_x1 = rad(x1)
    rad_x2 = rad(x2)
    a = rad_x1 - rad_x2
    b = rad(y1) - rad(y2)
    s = 2 * asin(sqrt(pow(sin(a/2),2)+cos(rad_x1)*cos(rad_x2)*pow(sin(b/2),2)))
    s = s * 6378.137
    s = round( s * 10000 ) / 10000
    return s

def plot_tsp_result(city_info, city_ids):
    import matplotlib.pyplot as plt
    x = []
    y = []
    for c_id in city_ids:
        x.append(city_info[c_id][0])
        y.append(city_info[c_id][1])
    x.append(x[0])
    y.append(y[0])

    plt.plot(x, y, 'ro-')
    plt.ylabel('y')
    plt.xlabel('x')
    plt.grid(True)
    plt.show()

def plot_ga_result(statistics):
    import matplotlib.pyplot as plt

    gen = []
    bests = []
    worsts = []
    avgs = []

    avg_time_per_gen = 0
    for key, value in statistics.items():
        if key != "avg_time_per_gen":
            gen.append(key)
            bests.append(value["best"])
            worsts.append(value["worst"])
            avgs.append(value["avg"])
        elif key == "avg_time_per_gen":
            avg_time_per_gen = value

    arrow_idx = int(len(gen) * 0.7)
    arrow_x = gen[arrow_idx]
    arrow_y = bests[arrow_idx]
    plt.plot(gen, bests, 'g-')
    plt.annotate("best", xy=(arrow_x, arrow_y,))

    arrow_y = worsts[arrow_idx]
    plt.plot(gen, worsts, 'r-')
    plt.annotate("worst", xy=(arrow_x, arrow_y))

    arrow_y = avgs[arrow_idx]
    plt.plot(gen, avgs, "b-")
    plt.annotate("avg", xy=(arrow_x, arrow_y))

    plt.ylabel("Fitness")
    plt.xlabel("Generation")

    xmin, xmax, ymin, ymax = plt.axis()
    textX = abs(xmax - xmin) * 0.1
    textY = abs(ymax) * 0.95
    plt.text(textX, textY, "avg time per gen: %f (sec.)"%(avg_time_per_gen))
    plt.grid(True)
    plt.show()

def calculate_estimated_kernel_usage(prog, ctx, kernel_name):
    try:
        import pyopencl as cl
        from pyopencl import context_info as ci
        from pyopencl import kernel_work_group_info as kwgi
        devices = ctx.get_info(ci.DEVICES)
        assert len(devices) == 1, "Should only one device is used !"
        device = devices[0]
        # for name in kernel_names:
        kernel = cl.Kernel(prog, kernel_name)
        # gws = kernel.get_work_group_info(kwgi.GLOBAL_WORK_SIZE, device)
        lm = kernel.get_work_group_info(kwgi.LOCAL_MEM_SIZE, device)
        pm = kernel.get_work_group_info(kwgi.PRIVATE_MEM_SIZE, device)
        cwgs = kernel.get_work_group_info(kwgi.COMPILE_WORK_GROUP_SIZE, device)
        pwgsm = kernel.get_work_group_info(kwgi.PREFERRED_WORK_GROUP_SIZE_MULTIPLE, device)

        print('For kernel "{}" running on device {}:'.format(kernel.function_name, device.name))
        # print('\t Max work size: {}'.format(gws))
        print('\t Max work-group size: {}'.format(cwgs))
        print('\t Recommended work-group multiple: {}'.format(pwgsm))
        print('\t Local mem used: {} of {}'.format(lm, device.local_mem_size))
        print('\t Private mem used: {}'.format(pm))
        return cwgs, pwgsm, lm, pm
    except:
        import traceback
        traceback.print_exc()
        return None, None, None, None
