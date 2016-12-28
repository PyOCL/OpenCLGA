# oclGA
oclGA is a python library for running genetic algorithm among Open CL devices, like GPU, CPU, DSP, etc. In the best case, you can run your GA parallelly at all of your Open CL devices which give you the maximum computing power of your machine. In the worse case, which you only have CPU, you still can run the code at parallel CPU mode.

We had implemented OpenCLGA at oclGA.py which encapsulate GA follow (population, crossover, mutation, fitness calculation). User could solve their problem by providing the fitness calculation function and run the code.

Please note that oclGA is implemented at Python 3.5 or above. It should work at Python 2.x but it is not guaranteed.

# Prerequisite: install PYOPENCL

Option A. Refers to https://wiki.tiker.net/PyOpenCL

Option B. My personal experience on Windows (just to install all required stuff in a quick way)

    -- Step 1. Install platform opencl graphic driver, e.g. Intel CPU or Intel HD Grahics (https://software.intel.com/en-us/intel-opencl)

    -- Step 2. Install the following *\*.whl* for python from

        1) http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy

        2) http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyopencl

# Try it out

1. Create virtual env (optional):

```shellscript
    mkdir oclGA
    virtualenv .
    source Scripts/activate
```

2. Install the pyopencl from 1) http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy and 2) http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyopencl

```
    pip install numpy-1.11.3+mkl-cp35-cp35m-win_amd64.whl
    pip install pyopencl-2016.2.1+cl12-cp35-cp35m-win_amd64.whl
```

3. Download the code from Github: https://github.com/PyOCL/oclGA/archive/master.zip

4. Execute the code

```
    unzip oclGA-master.zip
    cd oclGA-master
    python examples/tsp/simple_tsp.py
```


