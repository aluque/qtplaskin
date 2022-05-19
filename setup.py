# -*- coding: utf-8 -*-
"""
QtPlaskin

A graphical tool to explore ZdPlaskin Results

https://github.com/aluque/qtplaskin

Written by Alejandro Luque

---

Updated by Erwan Pannier, 2016 to turn it into an app

Note: you still have to install PyQt4 manually as it cannot be installed
from pip. Read Alejandro's INSTALL.txt file to see how to install PyQt4. 
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
    try:
        import pyqt
    except ImportError:
        raise ImportError("Please install these librairies manually first (with Anaconda is "+\
                        "strongly recommended) \n >>> conda install pyqt")

long_description = 'A graphical tool to explore ZdPlaskin Results'
if os.path.exists('README.md'):
    long_description = codecs.open('README.md', encoding="utf-8").read()

setup(name='qtplaskin',
      version='1.1.2',
      description='A graphical tool to explore ZdPlaskin Results',
      long_description=long_description,
      url='https://github.com/erwanp/qtplaskin',
      author='Alejandro Luque. Turned into a Python package by Erwan Pannier',
      author_email='erwan.pannier@gmail.com',
      install_requires=[
          'future',  # for builtins
          'numpy',
          'scipy',
          'matplotlib>=3.4.3',
          'h5py',
          'mpldatacursor',
          'pandas>=1.0',
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
          "Operating System :: OS Independent"],
      packages=['qtplaskin'],
      scripts=[
          'scripts/qtplaskin'],
      include_package_data=True,
      entry_points={"console_scripts": ["realpython=qtplaskin.main:main"]},
      zip_safe=False)
