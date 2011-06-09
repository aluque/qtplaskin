import sys
import os
import time
from multiprocessing import Process, Pipe

import numpy as np
import h5py

from runner import run

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
        for k in self.conditions:
            cond.create_dataset(k, data=self.condition(k), compression='gzip')

        dens = g.create_group('density')

        for i, species in enumerate(self.species):
            print "Writing density of species `%s'" % species
            ds = dens.create_dataset(species, data=self.density(species),
                                     compression='gzip')
            ds.attrs['index'] = [i,]
            
        dens = g.create_group('rate')

        for i, reaction in enumerate(self.reactions):
            try:
                ds = dens.create_dataset(reaction, data=self.rate(reaction),
                                         compression='gzip')
                ds.attrs['index'] = [i,]
                print "Writing reaction `%s'" % reaction
            except (RuntimeError, ValueError):
                ds = dens[reaction]
                ds.attrs['index'] += [i,]                
                print "Skipping repeated reaction `%s'" % reaction

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
            print "Writing density of species `%s'" % species
            dens.create_dataset(species, data=self.density(species),
                                compression='gzip')
            

        dens = g.create_group('rate')

        for reaction in self.reactions:
            try:
                dens.create_dataset(reaction, data=self.rate(reaction),
                                    compression='gzip')
                print "Writing reaction `%s'" % reaction
            except (RuntimeError, ValueError):
                print "Skipping repeated reaction `%s'" % reaction


        gsources = g.create_group('source')

        for species in self.species:
            print "Writing sources for species `%s'" % species
            s_group = gsources.create_group(species)

            react_dict = self.sources(species)
            for reaction, rate in react_dict.iteritems():
                print "   Writing reaction `%s'" % reaction
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

        self.species = list(self.h5_density)
        self.reactions = list(self.h5_rate)
        self.conditions = list(self.h5_condition)

        self.t = np.array(self.h5['main']['t'])
        self.source_matrix = np.array(self.h5['main']['source_matrix'])

        # We need those indices that tell us the order of the original lists
        # Note that the lookup order is inverted.

        # For the species we get a local index and we want an original index.
        # This works because there are no repeated species
        self.species_index = [None for _ in self.species]
        for i, species in enumerate(self.species):
            indices = self.h5_density[species].attrs['index']
            self.species_index[i] = indices[0]
         
        # For the reactions we need the inverse lookup.  And not that here
        # there may be repeated reactions
        self.reaction_index = {}
        for i, reaction in enumerate(self.reactions):
            indices = self.h5_rate[reaction].attrs['index']
            for j in indices:
                self.reaction_index[j] = i

        
        super(HDF5Data, self).__init__()


    def density(self, key):
        return np.array(self.h5_density[key])


    def rate(self, key):
        return np.array(self.h5_rate[key])


    def condition(self, key):
        return np.array(self.h5_condition[key])
    
        
    def sources(self, key):
        si = self.species_index[self.d_species[key]]
        c = self.source_matrix[si, :]
        d = {}
        for ri in np.nonzero(c)[0]:
            local_ri = self.reaction_index[ri]
            reaction = self.reactions[local_ri]
            d[reaction] = self.rate(reaction) * c[ri]

        return d




class ResultsData(ModelData):
    """ ModelData from a Results object. """
    def __init__(self, res):
        self.res = res

        self.species = res.species
        self.reactions = res.reactions
        self.source_matrix = res.source_matrix
        self.conditions = res.conditions.keys()
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
    some zdplaskin code:

    species_list.txt
    reactions_list.txt
    conditions_list.txt
    out_density.txt
    out_rate.txt
    source_matrix.txt
    out_temperatures.txt
    
    """
    
    def __init__(self, dirname):
        self.dirname = dirname

        with open(self._path('species_list.txt')) as fp:
            self.species = [s.strip() for s in fp.read().strip().split('\n')]

        with open(self._path('reactions_list.txt')) as fp:
            self.reactions = [s.strip() for s in fp.read().strip().split('\n')]

        with open(self._path('conditions_list.txt')) as fp:
            self.conditions = [s.strip() for s in fp.read().strip().split('\n')]

        
        self.n_species = len(self.species)
        self.n_reactions = len(self.reactions)

        self.update()

        super(DirectoryData, self).__init__()

    def update(self):
        _raw_density = np.loadtxt(self._path('out_density.txt'), skiprows=1)

        i_dens = _raw_density.shape[0]

        _raw_rates = np.loadtxt(self._path('out_rate.txt'), skiprows=1)

        self.source_matrix = np.loadtxt(self._path('source_matrix.txt'),
                                        dtype='d')

        _raw_conditions = np.loadtxt(self._path('out_temperatures.txt'),
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
        return self.raw_density[:, self.d_species[key]]


    def rate(self, key):
        return self.raw_rates[:, self.d_reactions[key]]


    def condition(self, key):
        return self.raw_conditions[:, self.d_conditions[key]]


    def sources(self, key):
        si = self.d_species[key]
        c = self.source_matrix[si, :]
        d = {}
        for ri in np.nonzero(c)[0]:
            d[self.reactions[ri]] = self.raw_rates[:, ri] * c[ri]

        return d
    


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
        self.conditions = self.conditions_dict.keys()
        

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
        return self.raw_density[:self.i, self.d_species[key]]
