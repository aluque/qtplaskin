# -*- coding: utf-8 -*-
"""
Created on Sun Mar 13 07:49:41 2016

@author: erwan

Import qtplaskin results in a Python environnement

TODO: timer between numpy reading speed from Qtplaskin and pandas performances
"""


import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
#import publib

foutn = 'qt_densities.txt'
fspe = 'qt_species_list.txt'
foutc = 'qt_conditions.txt'
fcond = 'qt_conditions_list.txt'


class QtParser():

    def __init__(self, folder):

        species = pd.read_csv(os.path.join(folder, fspe), delim_whitespace=True,
                              header=None)[1]

        species = list(species)

        header = ['t'] + species

        dens = pd.read_csv(os.path.join(folder, foutn), delim_whitespace=True,
                           skiprows=1, names=header)

        conditions_list = pd.read_csv(os.path.join(folder, fcond), delim_whitespace=True,
                                      header=None)[1]

        conditions_list = list(conditions_list)

        header = ['t'] + conditions_list

        conditions = pd.read_csv(os.path.join(folder, foutc), delim_whitespace=True,
                                 skiprows=1, names=header)

        self.species = species
        self.n = dens
        self.t = np.array(dens['t'])
        self.conditions_list = conditions_list
        self.conditions = conditions

    def get(self, species):
        ''' Get a given set species

        Input:
        -------

        species: list'''

        if not type(species) == list:
            return self.n[species]

        else:
            return [self.n[s] for s in species]

    def getcond(self, conditions):
        ''' Get a given set conditions

        Input:
        -------

        species: list'''

        if not type(conditions) == list:
            return self.conditions[conditions]

        else:
            return [self.conditions[c] for c in conditions]

    def plot(self, species):
        ''' Plot a given set species

        Input:
        -------

        species: list'''

        if not type(species) == list:
            species = [species]

        for s in species:
            if not s in self.species:
                raise ValueError(
                    '{0} not in species list: \n{1}'.format(s, self.species))

        fig, ax = plt.subplots()

        for s in species:
            ax.plot(self.t * 1e9, np.array(self.n[s]), '-o', label=s)
        ax.set_xlabel('t [ns]')
        ax.set_ylabel('Density [cm-3]')
        ax.legend()

    def plotc(self, conditions):
        ''' Plot a given set species

        Input:
        -------

        species: list'''

        if not type(conditions) == list:
            conditions = [conditions]

        for s in conditions:
            if not s in self.conditions_list:
                raise ValueError('{0} not in conditions list: \n{1}'.format(
                    s, self.conditions_list))

        fig, ax = plt.subplots()

        for s in conditions:
            ax.plot(self.t * 1e9, np.array(self.conditions[s]), '-o', label=s)
        ax.set_xlabel('t [ns]')
        ax.set_ylabel(s)
        ax.legend()


if __name__ == '__main__':

    f0 = '/home/cedric/Modelisation_ZDPlasKin/CO2/reduced_model_2/Param/ResultsParam/'

    T = ((300, 100),
         (300, 110),
         (300, 120),
         (300, 130),
         (300, 140),
         (300, 150),
         (300, 160),
         (300, 170),
         (400, 100),
         (400, 110),
         (400, 120),
         (400, 130),
         (400, 140),
         (400, 150),
         (500, 100),
         (500, 110),
         (500, 120),
         (500, 130),
         (500, 140),
         (500, 150),
         (500, 160),
         (500, 170),
         (600, 140),
         (600, 150),
         (600, 160),
         (600, 170),
         (700, 140),
         (700, 150),
         (700, 160),
         (700, 170),
         (800, 140),
         (800, 150),
         (800, 160),
         (800, 170),
         (900, 140),
         (900, 150),
         (900, 160)
         )

    out = {}

    for Ti, Tdi in T:

        folder = f0 + 'T=%sK_EN=0%sTd/' % (Ti, Tdi)
        Q = QtParser(folder)
        indEndOfPulse = np.argmax(Q.t > 1e-3)
        a = Q.getcond('Energy')  # energy efficiency
        b = Q.getcond('SEI')
        c = Q.getcond('Dissociation')  # dissociation rate
        d = Q.get('E')
        # Q.plotc('average')
        e = Q.getcond('Reduced')
        neMax = max(d)
        EN = max(e)
        out[(Ti, Tdi)] = list((EN, a[indEndOfPulse], b[
            indEndOfPulse], c[indEndOfPulse], neMax))
        print(Ti, Tdi)
        #efficiency = a[np.argmax(Q.t>1e-3)]

    k = 0
    for Ti, Tdi in T:
        out[(Ti, Tdi)].insert(0, Ti)
        print(out[(Ti, Tdi)])
    # print(Q.species

    #df = pd.read_csv(os.path.join(['Results',folder,foutn]))
