# TSP
Solving TSP (travelling salesman problem) via genetic algorithm &amp; opencl

概念 (IDEA) :

提供基本的 Gene 類別, Chromosome 類別, BaseGenericAlgorithm 類別,
將基因演算法的基本流程(競擇, 交配, 繁衍, 突變)封裝起來,
用意是希望使用者只需要繼承 BaseGenericAlgorithm 而不用修改 Gene/Chromosome 的前提下完成演算.

To provide basic classes Gene, Chromosome, BaseGenericAlgorithm, and encapsulate the basic follow (Selection, Crossover, Reproduction, Mutation) of GA. User could solve their problem by deriving BaseGenericAlgorithm without any modification to Gene/Chromosome classes.

例如  e.g.

Gene contains a DNA sequence, Gene1["A", "C", "T", "G"], Gene2["A", "T", "G", "C"], ...

Chromosome contains a list of Genes [G1, G2, G3, G4], and the DNA sequence looks like [["A", "C", "T", "G"], ["A", "T", "G", "C"], ...],

針對任一種最佳化問題, 只需要繼承 BaseGenericAlgorithm 類別, 並覆寫 evaluate_fitness 函數 (計算該代所有 Chromosomes 的基因序列之適應值), 並可透過 |set_customized_crossover_func|, |set_customized_mutate_func| 針對問題客製化交配,突變函數.

To solve an optimization problem, all you need is to design a good representation of DNA about the answer to your problem, and then to subclass BaseGenericAlgorithm, and override |evalutae_fitness|, also it's flexible to customized your own crossover,mutation function by invoking |set_customized_crossover_func|, |set_customized_mutate_func|.


# HOW TO RUN PYOPENCL

Option A. Refers to https://wiki.tiker.net/PyOpenCL

Option B. My personal experience (just to install all required stuff in a quick way)

    -- Step 1. Install platform opencl graphic driver, e.g. Intel CPU or Intel HD Grahics (https://software.intel.com/en-us/intel-opencl)

    -- Step 2. Install the following *\*.whl* for python from http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyopencl
    
        1) http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy
        
        2) http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyopencl
     
# Issues to be addressed

1. A better random number generator for OpenCL kernel.

2. The capability of customized mutation/crossover/fitness calculation for the GA algorithm in OpenCL kernel.

3. Dynamic workgroup size(global/local workitem) management.
