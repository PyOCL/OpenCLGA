# We need to put ancenstor directory in sys.path to let us import utils and algorithm
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if __name__ == '__main__':
    from ocl_ga_client import start_ocl_ga_client
    start_ocl_ga_client()
