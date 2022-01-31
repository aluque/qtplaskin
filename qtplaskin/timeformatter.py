# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 23:47:41 2016

@author: erwan
"""

from matplotlib.ticker import ScalarFormatter


class TimeFormatter(ScalarFormatter):
    ''' A class to display time axis with dynamic time units when you
    zoom in (ns, µs, ms...)

    Use
    -------

    time data has to be in seconds (s).

    >>> ax.xaxis.set_major_formatter(TimeFormatter().simple_function)

    In order to avoid errors, set the axis before plotting data.

    '''

    # pylint: disable=unused-argument
    @staticmethod
    def simple_function(time, pos, number_after_decimals=0):
        """Function to be used with ax.xaxis.set_major_formatter


        Args:
            time (float): the time (in s)
            pos ([type]): not used here, but needed by matplotlib
            number_after_decimals (int, optional): number after decimal displayed. Defaults to 0.

        Returns:
            str: time in a more readable way
        """
        x_label = ''

        precision = "." + str(number_after_decimals) + "f"
        if time < 1e-9:
            x_label = f"{time * 1e12:{precision}} ps"
        elif time < 1e-6:
            x_label = f"{time * 1e9:{precision}} ns"
        elif time < 1e-3:
            x_label = f"{time * 1e6:{precision}} µs"
        elif time < 1:
            x_label = f"{time * 1e3:{precision}} ms"
        else:
            x_label = f"{time:.2f} s"
        return x_label
