import random
from math import pi, sqrt, asin, cos, sin, pow

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

def plot_result(city_info, city_ids):
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
    plt.show()


def calculate_estimated_kernel_usage(prog, ctx, kernel_names):
    try:
        import pyopencl as cl
        from pyopencl import context_info as ci
        from pyopencl import kernel_work_group_info as kwgi
        devices = ctx.get_info(ci.DEVICES)
        assert len(devices) == 1, "Should only one device is used !"
        device = devices[0]
        for name in kernel_names:
            kerKer = cl.Kernel(prog, name)
            lm = kerKer.get_work_group_info(kwgi.LOCAL_MEM_SIZE, device)
            pm = kerKer.get_work_group_info(kwgi.PRIVATE_MEM_SIZE, device)
            cwgs = kerKer.get_work_group_info(kwgi.COMPILE_WORK_GROUP_SIZE, device)
            pwgsm = kerKer.get_work_group_info(kwgi.PREFERRED_WORK_GROUP_SIZE_MULTIPLE, device)
            print("[%s]\tEstimated usage : Local mem (%d)/ Private mem (%d)"\
                  "/ Compile WG size (%s)/ Preffered WG size multiple (%d)"\
                  %(name, lm, pm, str(cwgs), pwgsm))
    except:
        import traceback
        traceback.print_exc()
