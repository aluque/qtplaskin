# -*- coding: utf-8 -*-
"""
QtPlaskin

A graphical tool to explore ZdPlaskin Results

https://github.com/aluque/qtplaskin

Written by Alejandro Luque (2012)

---

Updated by Erwan Pannier (2016-2018) to turn it into a Python library

Note: you still have to install PyQt5 manually as it cannot be installed
from pip. Read Alejandro's INSTALL.txt file to see how to install PyQt. 
Note that although PyQt cannot be installed through pip, you can install
if with "conda install pyqt" if you're using the Anaconda distribution of 
Python


"""

from __future__ import absolute_import

import os
from setuptools import setup
import codecs

# Force installation of some librairies that cannot be installed with pip 
try:
    import PyQt5
except ImportError:
    raise ImportError("Please install these librairies manually first (with Anaconda is "+\
                        "strongly recommended) \n >>> conda install pyqt")

long_description = 'A graphical tool to explore ZdPlaskin Results'
if os.path.exists('README.md'):
    long_description = codecs.open('README.md', encoding="utf-8").read()

setup(name='qtplaskin',
      version='1.1.0',
      description='A graphical tool to explore ZdPlaskin Results',
      long_description=long_description,
      url='https://github.com/aluque/qtplaskin',
      author='Alejandro Luque, updated Erwan Pannier',
      author_email='luquex@gmail.com',
      install_requires=[
          'future',  # for builtins
          'numpy',
          'scipy',
          'matplotlib',
          'h5py',
          'mpldatacursor',
          # 'pyqt'      # cannot be installed through pip. Install PyQt5 manually
      ],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          "Operating System :: OS Independent"],
      packages=['qtplaskin'],
      scripts=[
          'scripts/qtplaskin'],
      include_package_data=True,
      zip_safe=False)
