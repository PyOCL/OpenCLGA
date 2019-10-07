# -*- coding: utf-8 -*-
import os
import sys
from setuptools import setup, find_packages

# We intend to support Python 3.5+, let's get rid of 2.x !
if (sys.version_info[0], sys.version_info[1]) <= (3, 4):
    sys.exit('Sorry, only Python 3.5+ is supported')

package_files_paths = []
def package_files(directory):
    global package_files_paths
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            if filename == '.gitignore':
                continue
            print(filename)
            package_files_paths.append(os.path.join('..', path, filename))

package_files('OpenCLGA/ui')
package_files('OpenCLGA/kernel')

setup(name='OpenCLGA',
      version='0.1',
      description='Run a general purpose genetic algorithm on top of pyopencl.',
      url='https://github.com/PyOCL/OpenCLGA.git',
      author='John Hu(胡訓誠), Kilik Kuo(郭彥廷)',
      author_email='im@john.hu, kilik.kuo@gmail.com',
      license='MIT',
      include_package_data=True,
      packages=find_packages(),
      package_data={
        'OpenCLGA': package_files_paths,
      },
      install_requires=[
          'pybind11'
          'matplotlib',
          'numpy',
          'pyopencl'
      ],
      zip_safe=False)
