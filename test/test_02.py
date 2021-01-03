# -*- coding: utf-8 -*-

from qtplaskin.modeldata import FastDirData, DirectoryData
from qtplaskin.main import select_rates
from os.path import join, abspath, dirname

from numpy.testing import assert_array_equal
from numpy import inf, nan, array

import pytest

test_arr = array([0.0, 1.0, inf, inf, -inf, nan], dtype=float)


@pytest.fixture
def fast_data():
    return FastDirData(join(abspath(dirname(__file__)), './data/02'))


@pytest.fixture
def slow_data():
    return DirectoryData(join(abspath(dirname(__file__)), './data/02'))


@pytest.mark.parametrize("specie, expected",
    [(1, test_arr), (2, test_arr[::-1]) ] )
def test_density_slow(slow_data, specie, expected):
    actual = slow_data.density(specie)
    assert_array_equal(expected, actual)


@pytest.mark.parametrize("cond, expected",
    [(1, test_arr), (2, test_arr[::-1]) ] )
def test_condition_slow(slow_data, cond, expected):
    actual = slow_data.condition(cond)
    assert_array_equal(expected, actual)


@pytest.mark.parametrize("rate, expected",
    [(1, test_arr)] )
def test_rate_slow(slow_data, rate, expected):
    actual = slow_data.condition(rate)
    assert_array_equal(expected, actual)


@pytest.mark.parametrize("specie, expected",
    [(1, test_arr), (2, test_arr[::-1]) ] )
def test_density_fast(fast_data, specie, expected):
    actual = fast_data.density(specie)
    assert_array_equal(expected, actual, err_msg="check if pandas>=1.0")


@pytest.mark.parametrize("cond, expected",
    [(1, test_arr), (2, test_arr[::-1]) ] )
def test_condition_fast(fast_data, cond, expected):
    actual = fast_data.condition(cond)
    assert_array_equal(expected, actual, err_msg="check if pandas>=1.0")


@pytest.mark.parametrize("rate, expected",
    [(1, test_arr)] )
def test_rate_fast(fast_data, rate, expected):
    actual = fast_data.condition(rate)
    assert_array_equal(expected, actual, err_msg="check if pandas>=1.0")