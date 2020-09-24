# QtPlaskin

QtPlaskin is a graphical interface to analyze results from a plasma 
kinetic code such as ZdPlasKin (1).  It supports both a specific data
format based on HDF5 and importing directories with certain filesets
that can be written from a running FORTRAN code.

Currently, QtPlaskin runs in Linux, Mac OS X and Windows but see the
file INSTALL.txt for information on the libraries that must be
installed in your system and how to obtain them.

With the latest version of ZDPlaskin you can use 

  call ZDPlaskin_set_config(QTPLASKIN_SAVE=.true.)

Then you can import the data of your simulation into QtPlaskin by using
File -> Import from directory... in the program menu.

The code was developed by Alejandro Luque at the Instituto de Astrofísica 
de Andalucía (IAA), CSIC and is licensed under the LGPLv3 License.

---

(1)  ZdPlaskin is a computer code developed by S. Pancheshnyi, B. Eismann, 
     G.J.M. Hagelaar and L.C. Pitchford, 
     http://www.zdplaskin.laplace.univ-tlse.fr (University of Toulouse, 
     LAPLACE, CNRS-UPS-INP, Toulouse, France, 2008).

---

### Recent Fork and community development

New features and small improvements were implemented by Community developers in the following fork : https://github.com/erwanp/qtplaskin

These features include :

- Dynamic tooltips on plots to analyze graphs with dozens of different lines

- Synchronized timescales over all plots, and dynamic ticks to deal with nanosecond to microsecond ranges

- ported to PyQt5 to keep up with the latest Python environnements

- Python3 compatible

- Made qtplaskin an installable Python library

- call qtplaskin from the command line with with qtplaskin $FOLDER to analyze a given directory

- faster Results folder loading using Pandas instead of Numpy

- more recent fork was I co-developed with some other developers : https://github.com/erwanp/qtplaskin

The new fork installs in one-line as a Python package. However, it does does not include packaged/executable files. 
Therefore you will need a Python environment installed (Anaconda or any scientific distribution is recommended).
For this reason it was never merged in the present version. 

If you want to contribute to the Community development of QtPlaskin, and make the new changes available for all, 
we definitly need some development help on making the new fork packaged/executable. Afterwards we would be able
to merge it.

Interested ? See more in https://github.com/aluque/qtplaskin/pull/5 and https://github.com/erwanp/qtplaskin/issues/17
