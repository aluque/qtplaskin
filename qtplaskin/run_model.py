'''
Script to initialize a ZdPlaskin session, run it and collect the results 

'''


import sys
import os
from optparse import OptionParser
from warnings import warn
import time
from multiprocessing import Process, Pipe
from collections import namedtuple

from numpy import inf
import scipy.constants as co

from qtplaskin import config
from qtplaskin.modeldata import ResultsData
from qtplaskin.runner import run

# Default name of the file to read densities from
DEF_INIT_DENS_FILE = 'init_species.dat'

tracked_conditions = ['gas_temperature',
                      'reduced_field',
                      'reduced_frequency',
                      'elec_temperature',
                      'elec_drift_velocity',
                      'elec_diff_coeff',
                      'elec_frequency_n',
                      'elec_power_n',
                      'elec_power_elastic_n',
                      'elec_power_inelastic_n']

# This is an object class to simplify the storage and passing of
# a simulation's results
Results = namedtuple('Results', ['t',
                                 'species',
                                 'reactions',
                                 'conditions',
                                 'density',
                                 'rates',
                                 'source_matrix'])


def receiver(conn):
    """ This function receives data from the running process and collects it.
    """

    # First we get t, the species list and the reactions list.
    t, species, reactions, source_matrix = conn.recv()
    n_species = len(species)
    n_reactions = len(reactions)

    # With that info we can already initialize the storage arrays
    density = zeros((t.shape[0], n_species))
    rates = zeros((t.shape[0], n_reactions))
    conditions = dict((cond, zeros(t.shape))
                      for cond in tracked_conditions)

    # We will store sources in a list of dictionaries
    # e.g. rrt[index('E')][index('E + O2 -> 2E + O2^+')]
    # is the rate of creation of
    # electrons due to that reaction.  Only reactions with some effect
    # will appear as keys in the dictionary.
    sources = [dict() for s in species]
    try:
        while True:
            data = conn.recv()
            if data is None:
                # I have to do this bc conn.recv does not raise EOFError when
                # the other end is closed
                raise EOFError

            i, c_density, c_rates, c_conditions = data

            density[i, :] = c_density
            rates[i, :] = c_rates

            for k, a in conditions.iteritems():
                a[i] = c_conditions[k]

    except EOFError:
        pass

    res = Results(t=t,
                  species=species,
                  reactions=reactions,
                  conditions=conditions,
                  density=density,
                  rates=rates,
                  source_matrix=source_matrix)

    return res


def main():
    global zdplaskin
    parser = OptionParser()
    parser.add_option("-k", "--kinetics", dest="kinetics",
                      help="Use this kinetic module",
                      type="str", default=None)

    parser.add_option("-i", "--initial-densities", dest="init_dens_file",
                      help=("Read the initial densities from this file [%s]"
                            % DEF_INIT_DENS_FILE),
                      type="str", default=DEF_INIT_DENS_FILE)

    parser.add_option("--max-dt", dest="max_dt",
                      help=("Longest allowed dt."),
                      type="float", default=inf)

    parser.add_option("-o", "--output", dest="output",
                      help="Output (HDF5) file",
                      type="str", default='out.h5')

    (opts, args) = parser.parse_args()

    if opts.kinetics is None:
        sys.stderr.write(
            "You need to specify a kinetic module with -k module.\n")
        sys.exit(-1)

    try:
        field_file = args[0]
        species = args[1:]
    except IndexError:
        print(', '.join("'%s'" % s for s in modelspecies()))
        sys.exit(0)

    conn_recv, conn_send = Pipe(False)
    p = Process(target=run,
                args=(conn_send, opts.kinetics,
                      opts.init_dens_file, field_file),
                kwargs=dict(max_dt=opts.max_dt))

    p.start()

    res = receiver(conn_recv)
    data = ResultsData(res)
    data.save(opts.output)

    #save(res, opts.output)


if __name__ == '__main__':
    main()
