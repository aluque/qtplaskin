# -*- coding: utf-8 -*-

from qtplaskin.modeldata import FastDirData
from qtplaskin.main import select_rates

import pytest

@pytest.fixture
def data():
    return FastDirData('./data/01')

def test_X_sources_10pct(data):
    icreation, idestruct = select_rates(data, 1, 0.1, -1)  
    assert icreation == {3}
    assert idestruct == {1}
    
def test_X_sources_01pct(data):
    icreation, idestruct = select_rates(data, 1, 0.001, -1)  
    assert icreation == {3,4}
    assert idestruct == {1}

def test_X_sources_all (data):
    icreation, idestruct = select_rates(data, 1, 0.0, -1)  
    assert icreation == {3,4}
    assert idestruct == {1}   
    
def test_X1_sources_all (data):
    icreation, idestruct = select_rates(data, 2, 0.0, -1)  
    assert icreation == {1}
    assert idestruct == {2,4}
    
def test_X1_sources_10pct (data):
    icreation, idestruct = select_rates(data, 2, 0.1, -1)  
    assert icreation == {1}
    assert idestruct == {2}
    
def test_X1_sources_1pct (data):
    icreation, idestruct = select_rates(data, 2, 0.01, -1)  
    assert icreation == {1}
    assert idestruct == {2,4} 

def test_X2_sources_all (data):
    icreation, idestruct = select_rates(data, 3, 0.0, -1)  
    assert icreation == {2}
    assert idestruct == {3}
    
def test_X2_sources_10pct (data):
    icreation, idestruct = select_rates(data, 3, 0.1, -1)  
    assert icreation == {2}
    assert idestruct == {3} 

if __name__ == '__main__':
    pytest.main()
