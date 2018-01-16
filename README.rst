
Join us on  `slack <https://join.slack.com/t/pyopenclopt/shared_invite/enQtMjQyNjU3NDk1NTA5LWRiODY5NTY3N2Y4ODY3YmI5Zjg2NGI4Nzg1NTMzZDYyNjBkOTdhNzU4MzAxNDYwNmE2YzEzODMzNzQ5YWQyYzU>`_  (歡迎上 `slack <https://join.slack.com/t/pyopenclopt/shared_invite/enQtMjQyNjU3NDk1NTA5LWRiODY5NTY3N2Y4ODY3YmI5Zjg2NGI4Nzg1NTMzZDYyNjBkOTdhNzU4MzAxNDYwNmE2YzEzODMzNzQ5YWQyYzU>`_ 交流 !!)
===============
.. figure:: https://img.shields.io/badge/slack-n.n-pink.svg
    :target: https://pyopenclopt.slack.com/


OpenCLGA
===============
OpenCLGA is a python library for running genetic algorithm among Open CL devices, like GPU, CPU, DSP, etc. In the best case, you can run your GA parallelly at all of your Open CL devices which give you the maximum computing power of your machine. In the worse case, which you only have CPU, you still can run the code at parallel CPU mode.

We had implemented OpenCLGA at ocl_ga.py which encapsulate GA follow (population, crossover, mutation, fitness calculation). User could solve their problem by providing the fitness calculation function and run the code.

Please note that OpenCLGA is implemented at Python 3.5 or above. It should work at Python 2.x but it is not guaranteed.


Demo Video
==============================
Taiwan Travel example: https://youtu.be/4pqmuV8RkMg

Prerequisite: install PYOPENCL
==============================
Option A. Please refer to https://wiki.tiker.net/PyOpenCL to find your OS or

Option B. Install by ourself

- Windows 10 (just to install all required stuff in a quick way)

  * Step 1. Install platform opencl graphic driver, e.g. Intel CPU or Intel HD Grahics (https://software.intel.com/en-us/intel-opencl), NVIDIA GPU Driver (https://developer.nvidia.com/opencl)

  * Step 2. Install the following `*.whl` for python from

     1. http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy

     2. http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyopencl

- Ubuntu 16.04

  * Step 1. Install platform OpenCL graphic driver, i.e.

     1. Intel CPU or Intel HD Graphics.

        a. `OpenCL™ 2.0 GPU/CPU driver package(SRB_4.1) for Linux* (64-bit) <https://software.intel.com/en-us/articles/opencl-drivers>`_

        b. `Installation instructions. <https://software.intel.com/en-us/articles/sdk-for-opencl-gsg-srb41>`_



  * Step 2. Download `Intel SDK for Application (2016 R3)& ICDs <https://software.intel.com/en-us/intel-opencl/download>`_ and install, if you have Intel devices : ::

      $> sudo apt-get install libnuma1 alien
      $> tar -xvf ./intel_sdk_for_opencl_2016_ubuntu_6.3.0.1904_x64.tgz
      $> cd ./intel_sdk_for_opencl_2016_ubuntu_6.3.0.1904_x64/rpm
      $> sudo alien opencl-2.1-intel-cpu-exp-6.3.0.1904-1.x86_64.rpm
      $> sudo dpkg -i opencl-2.1-intel-cpu-exp_6.3.0.1904-2_amd64.deb
      $> sudo apt-get install clinfo
      // To verify platform information from OpenCL
      $> clinfo

    You can verify the installed OpenCL driver is located in /opt/intel/ and the ICD loader is located in /etc/OpenCL/vendors.

  * Step 3. Create a virtual environment for pyopencl. ::

      // Make sure dependencies for building wheel is available on system.
      $> sudo apt-get install build-essential libssl-dev libffi-dev python-dev
      $> sudo apt-get install python3-pip python3-venv python3-tk ocl-icd-*
      $> python3 -m venv [NameOfEnv]
      $> source ./NameOfEnv/bin/activate
      <NameOfEnv>$> pip3 install --upgrade pip
      <NameOfEnv>$> pip3 install pyopencl

  * Step 4. Verification ::

      <NameOfEnv>$> python3
      > import pyopencl as cl
      > cl.create_some_context()

- Mac OS X

  * Step 1.
    Install Python3: since OpenCL drivers had already included in Mac OS X, we don't need to install any OpenCL driver by ourself. So, we can start from Python3. ::

      $> brew update
      $> brew install python3
      $> pip3 install virtualenv

    *Note that you may not need to install virtualenv if you already installed it with python 2.7.*

  * Step 2. Create a virtual environment for pyopencl: before install pyopencl, we may need to install XCode developer console tool with `xcode-select --install` command. If you already had it, you don't need to run it. ::

      $> python3 -m venv [NameOfEnv]
      $> source ./NameOfEnv/bin/activate
      <NameOfEnv>$> pip3 install --upgrade pip
      <NameOfEnv>$> pip3 install pycparser cffi numpy wheel
      <NameOfEnv>$> pip3 install pyopencl


  * Step 3. Verification. ::

      <NameOfEnv>$> python3
      > import pyopencl as cl
      > cl.create_some_context()

Run OpenCLGA examples
==============================
1. Enter virtual env (optional):

* For Windows with MinGW environment. ::

      $> source <NameOfEnv>/Scripts/activate

* For Linux/Mac OS X environment. ::

      $> source ./NameOfEnv/bin/activate


2. Download the code from `Github <https://github.com/PyOCL/OpenCLGA/archive/master.zip>`_ or git clone the repository via the following command. ::

      <NameOfEnv>$> git clone https://github.com/PyOCL/OpenCLGA.git

3. Install Extra package (optional) :

* For Linux environment. ::

      // To make matplotlib display correctly.
      $> sudo apt-get install python3-tk

4. Execute the code. ::

      <NameOfEnv>$> pip3 install git+git://github.com/PyOCL/OpenCLGA.git
      <NameOfEnv>$> unzip OpenCLGA-master.zip
      <NameOfEnv>$> cd OpenCLGA-master
      <NameOfEnv>$> python3 examples/tsp/simple_tsp.py

  *NOTE : In external process mode, if "no device" exception happen during create_some_context(), Please set PYOPENCL_CTX=N (N is the device number you want by default) at first.*

  *NOTE : Since we didn't publish this project to pipa. We need to install this project with source, `pip3 install .`.*
