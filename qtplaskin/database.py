#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Some physical values
"""

import re

# Constants

Na = 6.02214129e+23   
''' Avogadro number (molec/mole)'''


# Get parse atoms in molecule

_parse_molecule = re.compile('([A-Z][a-z]?)(\d+)?')

def get_atoms_in(molecule):
    
    out = dict(_parse_molecule.findall(molecule))
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
        }
''' molar mass in g/mol '''
  
def get_molecule(state):
    ''' Get molecule radical of ion / excited level '''
    
    return state.split('(')[0].split('^')[0]

def get_molar_mass(state):
    
    molecule = get_molecule(state)
    atoms_dict = get_atoms_in(molecule)
    return sum([_molar_mass_dict[k]*v for k,v in atoms_dict.items()])


# %% Some tests
    
def _test(*args, **kwargs):
    assert get_atoms_in('CO2') == {'C':1, 'O':2}
    assert get_molar_mass('CO2(v1)') == 44.0095
    assert get_molar_mass('N2+') == 28.0134
    

if __name__ == '__main__':
    # Some tests
    _test()