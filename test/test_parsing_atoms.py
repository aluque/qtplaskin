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
from qtplaskin.database import get_atoms_in, get_molar_mass


def test_if_unknown_atom_fails():
    state = 'Y'
    M=database.get_molar_mass(state, warn_err=False)
    assert isnan(M)

def test_if_Ar_is_recognized():
    """Two letters atom was not recognized.

    See https://github.com/erwanp/qtplaskin/pull/16"""
    FastDirData(join(abspath(dirname(__file__)), './data/two_letters_atom_failure'))

def test_parsing_atoms(*args, **kwargs):
    assert get_atoms_in('CO2') == {'C':1, 'O':2}
    assert get_atoms_in('CO2(V1)') == {'C':1, 'O':2}

def test_molar_mass(*args, **kwargs):
    assert get_molar_mass('CO2(v1)') == 44.0095
    assert get_molar_mass('N2+') == 28.0134



if __name__ == '__main__':
    pytest.main()