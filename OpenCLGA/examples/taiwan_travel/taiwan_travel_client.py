
if __name__ == "__main__":
    import os
    import sys
    # We need to put ancenstor directory in sys.path to let us import utils and algorithm
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from ocl_ga_client import start_ocl_ga_client
else:
    from ...ocl_ga_client import start_ocl_ga_client

def start_tt_client():
    start_ocl_ga_client()

if __name__ == '__main__':
    start_tt_client()
