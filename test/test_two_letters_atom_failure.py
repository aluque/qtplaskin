#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 16:49:19 2020

@author: jean
"""


from qtplaskin import FastDirData
from qtplaskin import database
from os.path import join, abspath, dirname
from numpy import isnan
import pytest

def test_if_unknown_atom_fails():
    state = 'Y'
    M=database.get_molar_mass(state, warn_err=False)  
    assert isnan(M)

def test_if_Ar_is_recognized():
    FastDirData(join(abspath(dirname(__file__)), './data/two_letters_atom_failure'))
    
    
if __name__ == '__main__':
    pytest.main()