# oclGA
oclGA is a python library for running genetic algorithm among Open CL devices, like GPU, CPU, DSP, etc. In the best case, you can run your GA parallelly at all of your Open CL devices which give you the maximum computing power of your machine. In the worse case, which you only have CPU, you still can run the code at parallel CPU mode.

We had implemented OpenCLGA at oclGA.py which encapsulate GA follow (population, crossover, mutation, fitness calculation). User could solve their problem by providing the fitness calculation function and run the code.

Please note that oclGA is implemented at Python 3.5 or above. It should work at Python 2.x but it is not guaranteed.

# Prerequisite: install PYOPENCL

Option A. Please refer to https://wiki.tiker.net/PyOpenCL to find your OS or

Option B. Install by ourself

- Windows 10 (just to install all required stuff in a quick way)

  * Step 1. Install platform opencl graphic driver, e.g. Intel CPU or Intel HD Grahics (https://software.intel.com/en-us/intel-opencl)

  * Step 2. Install the following *\*.whl* for python from

     1. http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy

     2. http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyopencl

- Ubuntu 16.04

   * Step 1. Install platform opencl graphic driver, e.g. Intel CPU or Intel HD Graphics (https://software.intel.com/en-us/intel-opencl/download)

   * Step 2. Install Intel OpenCL 2.1 Driver & ICD, if you use Intel devices:
   
    ```shellscript
        $> sudo apt-get install libnuma1 alien
        $> tar -xvf ./intel_sdk_for_opencl_2016_ubuntu_6.3.0.1904_x64.tgz
        $> cd ./intel_sdk_for_opencl_2016_ubuntu_6.3.0.1904_x64/rpm
        $> sudo alien opencl-2.1-intel-cpu-exp-6.3.0.1904-1.x86_64.rpm
        $> sudo dpkg -i opencl-2.1-intel-cpu-exp_6.3.0.1904-2_amd64.deb
        $> sudo apt-get install clinfo
        $> clinfo  # To verify platform information from OpenCL
    ```
    
    You can verify the installed OpenCL driver is located in /opt/intel/ and
    the ICD loader is located in /etc/OpenCL/vendors.

   * Step 3. Create a virtual environment for pyopencl.
   
    ```shellscript
        $> sudo apt-get install python3-pip python3-venv ocl-icd-*
        $> python3 -m venv [NameOfEnv]
        $> source ./NameOfEnv/bin/activate
        <NameOfEnv>$> pip3 install --upgrade pip
        <NameOfEnv>$> pip3 install pycparser cffi numpy wheel
        <NameOfEnv>$> pip3 install pyopencl
    ```

   * Step 4. Verification
    
    ```shellscript
        <NameOfEnv>$> python3
        > import pyopencl as cl
        > cl.create_some_context()
    ```
    
- Mac OS X

    * Step 1. Install Python3
        Since OpenCL drivers had already included in Mac OS X, we don't need to install any OpenCL driver by ourself. So, we can start from Python3.
    ```
        $> brew update
        $> brew install python3
        $> pip3 install virtualenv
    ```
        Please note that you may not need to install virtualenv if you already installed it with python 2.7.
    
    * Step 2. Create a virtual environment for pyopencl.
        Before install pyopencl, we may need to install XCode developer console tool with `xcode-select --install` command. If you already had it, you don't need to run it.
    ```
        $> python3 -m venv [NameOfEnv]
        $> source ./NameOfEnv/bin/activate
        <NameOfEnv>$> pip3 install --upgrade pip
        <NameOfEnv>$> pip3 install pycparser cffi numpy wheel
        <NameOfEnv>$> pip3 install pyopencl
    ```
    
    * Step 3. Verification
    ```shellscript
        <NameOfEnv>$> python3
        > import pyopencl as cl
        > cl.create_some_context()
    ```    

# Run oclGA examples

1. Enter virtual env (optional):

 * For Windows with MinGW environment

    ```shellscript
        $> source <NameOfEnv>/Scripts/activate
    ```
  * For Linux enviornment
  
    ```shellscript
        $> source ./NameOfEnv/bin/activate
    ```

3. Download the code from Github: https://github.com/PyOCL/oclGA/archive/master.zip or clone the git repo with the following command:

   ```shellscript
       <NameOfEnv>$> git clone https://github.com/PyOCL/oclGA.git
   ```

4. Execute the code

    ```shellscript
        <NameOfEnv>$> unzip oclGA-master.zip
        <NameOfEnv>$> cd oclGA-master
        <NameOfEnv>$> python3 examples/tsp/simple_tsp.py
    ```
