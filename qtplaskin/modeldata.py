import sys
import os
import time
from multiprocessing import Process, Pipe

import numpy as np
import pandas as pd
import h5py

from qtplaskin.runner import run


class ModelData(object):
    """ This class abstracts the reading of model data and its output
    to an HDF5 file.  These are the common methods. """
    def __init__(self):
        # Lookup of species and reaction indices
        self.d_species = dict((k, i) for i, k in enumerate(self.species))
        self.d_reactions = dict((k, i) for i, k in enumerate(self.reactions))
        self.d_conditions = dict((k, i) for i, k in enumerate(self.conditions))


    def flush(self):
        # This allows some kind of data sources where we have to flush.
        pass
    
    def update(self):
        pass
    
    def save(self, ofile, metadata={}):
        f = h5py.File(ofile, 'w')
        g = f.create_group('main')
        ref_dtype = h5py.special_dtype(ref=h5py.Reference)
        
        for k, val in metadata.iteritems():
            g.attrs[k] = val

        # We always write at least these two metadata
        g.attrs['command'] = ' '.join(sys.argv)
        g.attrs['timestamp'] = time.ctime()

        cond = g.create_group('condition')
        for i, condition in enumerate(self.conditions):
            ds = cond.create_dataset('%.4d' % (i + 1),
                                data=self.condition(i + 1), compression='gzip')
            ds.attrs['name'] = condition
            
        dens = g.create_group('density')

        for i, species in enumerate(self.species):
            print("Writing density of species `%s'" % species)
            ds = dens.create_dataset('%.4d' % (i + 1), data=self.density(i + 1),
                                     compression='gzip')
            ds.attrs['name'] = species
            
        dens = g.create_group('rate')

        for i, reaction in enumerate(self.reactions):
            try:
                ds = dens.create_dataset('%.4d' % (i + 1),
                                         data=self.rate(i + 1),
                                         compression='gzip')
                ds.attrs['name'] = reaction
                print("Writing reaction `%s'" % reaction)
            except (RuntimeError, ValueError):
                print("Error in reaction %d `%s'" % (i + 1, reaction))

        g.create_dataset('t', data=self.t)
        g.create_dataset('source_matrix', data=self.source_matrix,
                         compression='gzip')
       
        
    def old_save(self, ofile, metadata={}):
        """ Saves the data in an old format.
        and some metadata into output file ofile.
        """
        f = h5py.File(ofile, 'w')
        g = f.create_group('zdplaskin')

        for k, val in metadata.iteritems():
            g.attrs[k] = val

        # We always write at least these two metadata
        g.attrs['command'] = ' '.join(sys.argv)
        g.attrs['timestamp'] = time.ctime()

        g.create_dataset('t', data=self.t)

        cond = g.create_group('condition')
        for k in self.conditions:
            cond.create_dataset(k, data=self.condition(k), compression='gzip')

        dens = g.create_group('density')

        for species in self.species:
            print("Writing density of species `%s'" % species)
            dens.create_dataset(species, data=self.density(species),
                                compression='gzip')
            

        dens = g.create_group('rate')

        for reaction in self.reactions:
            try:
                dens.create_dataset(reaction, data=self.rate(reaction),
                                    compression='gzip')
                print("Writing reaction `%s'" % reaction)
            except (RuntimeError, ValueError):
                print("Skipping repeated reaction `%s'" % reaction)


        gsources = g.create_group('source')

        for species in self.species:
            print("Writing sources for species `%s'" % species)
            s_group = gsources.create_group(species)

            react_dict = self.sources(species)
            for reaction, rate in react_dict.iteritems():
                print("   Writing reaction `%s'" % reaction)
                try:
                    s_group.create_dataset(reaction.replace('.', '_'),
                                           data=rate, compression='gzip')
                except Exception:
                    warn("Ignoring repeated reaction '%s'" % reaction)
        f.close()


class HDF5Data(ModelData):
    """ ModelData from a HDF5 file. """
    def __init__(self, fname):
        self.fname = fname
        self.h5 = h5py.File(fname)
        self.h5_density = self.h5['main/density'] 
        self.h5_rate = self.h5['main/rate'] 
        self.h5_condition = self.h5['main/condition'] 

        self.species = self._read_datasets(self.h5_density)
        self.reactions = self._read_datasets(self.h5_rate)
        self.conditions = self._read_datasets(self.h5_condition)

        self.t = np.array(self.h5['main']['t'])
        self.source_matrix = np.array(self.h5['main']['source_matrix'])

        super(HDF5Data, self).__init__()


    def _read_datasets(self, group):
        sindices = list(group)
        sindices.sort()
        
        r = [group[s].attrs['name'] for s in sindices]

        return r
        
    @staticmethod
    def _index_key(i):
        return '%.4d' % i
        
    def density(self, key):
        return np.array(self.h5_density[self._index_key(key)])


    def rate(self, key):
        return np.array(self.h5_rate[self._index_key(key)])


    def condition(self, key):
        return np.array(self.h5_condition[self._index_key(key)])
    
        
    def sources(self, key):
        c = self.source_matrix[key - 1, :]
        d = {}
        for ri in np.nonzero(c)[0]:
            reaction = self.reactions[ri]
            d[ri] = self.rate(ri + 1) * c[ri]

        return d




class ResultsData(ModelData):
    """ ModelData from a Results object. """
    def __init__(self, res):
        self.res = res

        self.species = res.species
        self.reactions = res.reactions
        self.source_matrix = res.source_matrix
        self.conditions = list(res.conditions.keys())
        self.conditions_dict = res.conditions
        self.t = res.t
        
        self.raw_density = res.density
        self.raw_rates = res.rates
        
        super(ResultsData, self).__init__()


    def density(self, key):
        return self.raw_density[:, self.d_species[key]]


    def rate(self, key):
        return self.raw_rates[:, self.d_reactions[key]]


    def condition(self, key):
        return self.conditions_dict[key]
    
        
    def sources(self, key):
        si = self.d_species[key]
        c = self.source_matrix[si, :]
        d = {}
        for ri in np.nonzero(c)[0]:
            d[self.reactions[ri]] = self.raw_rates[:, ri] * c[ri]

        return d


class DirectoryData(ModelData):
    """ Modeldata from a file with these files, that have to be generated by
    some zdplaskin code

    species_list.txt
    reactions_list.txt
    conditions_list.txt
    out_density.txt
    out_rate.txt
    source_matrix.txt
    out_condition.txt (out_temperatures.txt would also work).
    
    """

    F_SPECIES_LIST = 'qt_species_list.txt'
    F_REACTIONS_LIST = 'qt_reactions_list.txt'
    F_CONDITIONS_LIST = 'qt_conditions_list.txt'
    F_DENSITIES = 'qt_densities.txt'
    F_RATES = 'qt_rates.txt'
    F_MATRIX = 'qt_matrix.txt'
    F_CONDITIONS = 'qt_conditions.txt'

    # If true, assumes that lists are numbered and ignores the leading number
    NUMBERED_LISTS = True
    
    def __init__(self, dirname):
        self.dirname = os.path.expanduser(dirname)

        self.species = self._read_list(self.F_SPECIES_LIST)
        self.reactions = self._read_list(self.F_REACTIONS_LIST)
        self.conditions = self._read_list(self.F_CONDITIONS_LIST)

        self.n_species = len(self.species)
        self.n_reactions = len(self.reactions)

        self.update()

        super(DirectoryData, self).__init__()

    def _read_list(self, fname):
        with open(self._path(fname)) as fp:
            r = [s.strip() for s in fp.read().strip().split('\n')]

        if self.NUMBERED_LISTS:
            r = [' '.join(s.split()[1:]) for s in r]

        # We use a dictionary here to allow arbitrary IDs.
        return r

    def update(self):
        """ Reads or re-reads those files that may change during the execution.
        """
        _raw_density = np.loadtxt(self._path(self.F_DENSITIES), skiprows=1)

        i_dens = _raw_density.shape[0]

        _raw_rates = np.loadtxt(self._path(self.F_RATES), skiprows=1)

        self.source_matrix = np.loadtxt(self._path(self.F_MATRIX),
                                        dtype='d')

        _raw_conditions = np.loadtxt(self._path(self.F_CONDITIONS),
                                     skiprows=1)

        latest_i = min(d.shape[0] for d in
                       (_raw_density, _raw_rates, _raw_conditions))

        self.raw_conditions = _raw_conditions[:latest_i, 1:]
        self.raw_rates = _raw_rates[:latest_i, 1:]
        self.raw_density = _raw_density[:latest_i, 1:]
        self.t = _raw_density[:latest_i, 0]
        

                                 
    def _path(self, fname):
        # This is just to save typing
        return os.path.join(self.dirname, fname)


    def density(self, key):
        return self.raw_density[:, key - 1]


    def rate(self, key):
        return self.raw_rates[:, key - 1]


    def condition(self, key):
        return self.raw_conditions[:, key - 1]


    def sources(self, key):
        # The +/-1 in this function are to move to the FORTRAN/ZdPlaskin
        # array numbering convention.
        c = self.source_matrix[key - 1, :]
        d = {}
        for ri in np.nonzero(c)[0]:
            d[ri] = self.raw_rates[:, ri] * c[ri]

        return d

class FastDirData(DirectoryData):
    """ An faster, updated version of DirectoryData using Pandas to read the 
    input files 
    
    Up to 5x faster on a ~1 Gb case (1.15 min -> 15 s) but not fully tested and 
    some features such as real time tracking may be broken.
    
    Problem with large sizes (>800 Mb) solved with chunking. 
    
    @erwanp 26/06/16"""

    def update(self):
        """ Reads or re-reads those files that may change during the execution.
        """
        _raw_density = pd.read_csv(self._path(self.F_DENSITIES), delim_whitespace=True,
                                   iterator=True, chunksize=50000)
        _raw_density = pd.concat(_raw_density, ignore_index=True) 
        _raw_density = np.array(_raw_density)

        i_dens = _raw_density.shape[0]

        _raw_rates = pd.read_csv(self._path(self.F_RATES), delim_whitespace=True, 
                                 iterator=True, chunksize=50000)
        _raw_rates = pd.concat(_raw_rates, ignore_index=True) 
        _raw_rates = np.array(_raw_rates)

        _source_matrix = pd.read_csv(self._path(self.F_MATRIX), delim_whitespace=True,
                                        dtype='d', header=None)
        self.source_matrix = np.array(_source_matrix)

        _raw_conditions = pd.read_csv(self._path(self.F_CONDITIONS), delim_whitespace=True,
                                 iterator=True, chunksize=50000)
        _raw_conditions = pd.concat(_raw_conditions, ignore_index=True) 
        _raw_conditions = np.array(_raw_conditions)

        latest_i = min(d.shape[0] for d in
                       (_raw_density, _raw_rates, _raw_conditions))

        self.raw_conditions = _raw_conditions[:latest_i, 1:]
        self.raw_rates = _raw_rates[:latest_i, 1:]
        self.raw_density = _raw_density[:latest_i, 1:]
        self.t = _raw_density[:latest_i, 0]
        
    # %% Plus add some convenient functions to work with data
        
        
    def get(self,species):
        ''' Get a given set species
        
        Input:
        -------
        
        species: list'''
        
        def _index(s):
            try:
                i = self.species.index(s)
            except ValueError:
                raise ValueError("%s not in species list: %s"%(s,self.species))
            return i
        
        latest_i = min(d.shape[0] for d in
                       (self._raw_density, self._raw_rates, self._raw_conditions))

        if not type(species)==list:
            return self.raw_density[:latest_i,_index(species)]
            
        else:
            return [self.raw_density[:latest_i,_index(s)] for s in species]
        
    def get_cond(self,conditions):
        ''' Get a given set conditions
        
        Input:
        -------
        
        species: list'''
        
        def _index(c):
            try:
                i = self.conditions.index(c)
            except ValueError:
                raise ValueError("%s not in conditions: %s"%(c,self.conditions))
            return i
        
        latest_i = min(d.shape[0] for d in
                       (self._raw_density, self._raw_rates, self._raw_conditions))

        if not type(conditions)==list:
            return self.raw_conditions[:latest_i,_index(conditions)]
            
        else:
            return [self.raw_conditions[:latest_i,_index(c)] for c in conditions]
     

    def plot(self,species):
        ''' Quickly plot a species directly from FastDirData. To be moved later
        in a separate batch interface module '''
        
        import matplotlib.pyplot as plt
        plt.plot(self.t,self.get(species))



class OldDirectoryData(DirectoryData):
    """ A backwards-compatible version of DirectoryData (deprecated).
    """

    F_SPECIES_LIST = 'species_list.txt'
    F_REACTIONS_LIST = 'reactions_list.txt'
    F_CONDITIONS_LIST = 'conditions_list.txt'
    F_DENSITIES = 'out_density.txt'
    F_RATES = 'out_rate.txt'
    F_MATRIX = 'source_matrix.txt'
    F_CONDITIONS = 'out_temperatures.txt'

    NUMBERED_LISTS = False


class RealtimeData(ModelData):
    tracked_conditions =  ['gas_temperature',
                           'reduced_field',
                           'reduced_frequency',
                           'elec_temperature',
                           'elec_drift_velocity',
                           'elec_diff_coeff',
                           'elec_frequency_n',
                           'elec_power_n',
                           'elec_power_elastic_n',
                           'elec_power_inelastic_n']

    def __init__(self, *args, **kwargs):
        # The arguments are passed to run.
        self.conn, self.conn_child = Pipe()
        self.sub = Process(target=run, args=(self.conn_child,) + args,
                           kwargs=kwargs)
        self.sub.start()

        # With the subprocess already running, we can already ask for some data
        # First we get t, the species list and the reactions list.
        self.t_, self.species, self.reactions = self.conn.recv()
        n_species = len(self.species)
        n_reactions = len(self.reactions)
        
        # With that info we can already initialize the storage arrays
        self.raw_density = np.zeros((self.t_.shape[0], n_species))
        self.raw_rates = np.zeros((self.t_.shape[0], n_reactions))
        self.conditions_dict = dict((cond, np.zeros(self.t_.shape))
                                    for cond in self.tracked_conditions)
        self.conditions = list(self.conditions_dict.keys())
        

        # We will store sources in a list of dictionaries
        # e.g. rrt[index('E')][index('E + O2 -> 2E + O2^+')]
        # is the rate of creation of
        # electrons due to that reaction.  Only reactions with some effect
        # will appear as keys in the dictionary.
        self.sources = [dict() for s in self.species]

        # This indicates how much data has been read
        self.i = 0

        super(RealtimeData, self).__init__()


    @property
    def t(self):
        return self.t_[:self.i]

    
    def flush(self, timeout=2):
        self.conn.send('flush')
        try:
            while self.conn.poll(timeout):
                data = self.conn.recv()
                if data is None:
                    # I have to do this bc conn.recv does not raise EOFError when
                    # the other end is closed
                    raise EOFError

                i, c_density, c_rates, c_rrt, c_conditions = data

                self.raw_density[i, :] = c_density
                self.raw_rates[i, :] = c_rates

                for k, a in self.conditions_dict.iteritems():
                    a[i] = c_conditions[k]

                # To save space we will store only nonzero species/reaction pairs
                for si, ri in zip(*np.nonzero(c_rrt)):
                    # si is the species index, ri is the reaction index
                    try:
                        self.sources[si][ri][i] = c_rrt[si, ri]
                        s = self.species[si]
                        r = self.reactions[ri]
                    except KeyError:
                        self.sources[si][ri] = np.zeros((self.t_.shape[0],))
                        self.sources[si][ri][i] = c_rrt[si, ri]

                self.i = i
        except EOFError:
            pass

        
    def density(self, key):
        return self.raw_density[:self.i, key]
