# We need to put ancenstor directory in sys.path to let us import utils and algorithm
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def show_generation_info(index, data_dict):
    msg = "{0}\t\t==> {1}".format(index, data_dict["best"])
    print(msg)

if __name__ == '__main__':
    from ocl_ga_client import start_ocl_ga_client
    start_ocl_ga_client()
