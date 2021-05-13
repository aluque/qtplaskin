#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Some physical values
"""

import re

# Constants

Na = 6.02214129e+23
''' Avogadro number (molec/mole)'''


def get_molecule(state):
    ''' Get molecule radical of ion / excited level '''

    return state.split('(')[0].split('^')[0]

# Get parse atoms in molecule

_parse_molecule = re.compile('([A-Z][a-z]?)(\d+)?')

def get_atoms_in(molecule):

    out = dict(_parse_molecule.findall(get_molecule(molecule)))
    for k, v in out.items():
        if v == '':
            out[k] = 1
        else:
            out[k] = int(v)
    return out

# get mole fractions

_molar_mass_dict = {
        'H':1.0079,
        'He':4.0026,
        'C':12.0107,
        'N':14.0067,
        'O':15.9994,
        'Ar':39.948,
        'X':0,   # virtual species
        'E':0,   # electron mass is neglected
        }
''' molar mass in g/mol '''

def get_molar_mass(state, warn_err=True):

    molecule = get_molecule(state)
    atoms_dict = get_atoms_in(molecule)
    try:
        return sum([_molar_mass_dict[k]*v for k,v in atoms_dict.items()])
    except KeyError as err:
        from numpy import nan
        from warnings import warn
        if warn_err:
            warn('Unknown molar mass for specie '+str(err))
        return(nan)


# %% Some tests

if __name__ == '__main__':

    import pytest

    print("Testing atom parsing:", pytest.main(["../test/test_parsing_atoms.py"]))