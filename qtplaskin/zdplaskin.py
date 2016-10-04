""" Wrapper module for zdplaskin. 
    (c) Alejandro Luque Estepa 2010
"""

from __future__ import print_function, division
from builtins import range

from warnings import warn

from numpy import ones
import sys


class Kinetics(object):
    DEFAULT_FIXED_DENS = {'N2': True,
                          'O2': True}

    def __init__(self, kinetics_name):
        """ Loads a kinetic module. """
        self.mod = __import__(kinetics_name).zdplaskin

        self.init = self.mod.zdplaskin_init
        self.set_conditions_ = self.mod.zdplaskin_set_conditions
        self.get_conditions_ = self.mod.zdplaskin_get_conditions
        self.set_density = self.mod.zdplaskin_set_density
        self.get_density_ = self.mod.zdplaskin_get_density
        self.get_density_total_ = self.mod.zdplaskin_get_density_total
        self.timestep = self.mod.zdplaskin_timestep
        self.reset = self.mod.zdplaskin_reset
        self.set_config = self.mod.zdplaskin_set_config
        self.write_file = self.mod.zdplaskin_write_file
        self.get_rates = self.mod.zdplaskin_get_rates
        self.reac_source_matrix = self.mod.zdplaskin_reac_source_matrix

        self.SPECIES = self.species()
        self.REACTIONS = self.reactions()

        self.N_SPECIES = len(self.SPECIES)
        self.N_REACTIONS = len(self.REACTIONS)

        # This uses the python/c convention, starting with index 1
        self.REACTION_INDEX = dict((r, i)
                                   for i, r in enumerate(self.REACTIONS))
        self.SPECIES_INDEX = dict((s, i) for i, s in enumerate(self.SPECIES))
        self.conditions = {
            'spec_heat_ratio': 1.4,
            'gas_heating': False,
            'soft_reset': False}
        self.conditions_set = False

    def species(self):
        """ Returns a list of all species in the kinetic module. """
        return [''.join(self.mod.species_name[:, i]).strip()
                for i in range(self.mod.species_max)]

    def reactions(self):
        """ Returns a list of all reactions in the module. """
        return [''.join(self.mod.reaction_sign[:, i]).strip()
                for i in range(self.mod.reactions_max)]

    def get_density(self, s):
        """ Gets density of species s. """
        return self.get_density_(s)[0]

    def get_reaction_rates(self):
        """ Returns a list of all rates. """
        _, rates, _, _, _, _, _ = self.get_rates()
        return rates

    def get_rates_list(self, lreact):
        """ Returns a list of selected rates. lreact is a list
        of reaction signatures. """
        rates = self.get_reaction_rates()
        return [rates[self.REACTION_INDEX[r]] for r in lreact]

    def get_conditions(self):
        """ Returns a dictionary with the zdplaskin conditions.  """

        conds = ['gas_temperature',
                 'reduced_frequency',
                 'reduced_field',
                 'elec_temperature',
                 'elec_drift_velocity',
                 'elec_diff_coeff',
                 'elec_frequency_n',
                 'elec_power_n',
                 'elec_power_elastic_n',
                 'elec_power_inelastic_n',
                 'elec_eedf']

        data = self.get_conditions_()
        d = dict(zip(conds, data))
        return d

    def set_conditions(self, **kwargs):
        """ Sets conditions for zdplaskin. """
        # Unfortunately, f2py does not support the present() fortran
        # construcition so we are forced to first ask for the conditions
        keys = ['gas_temperature',
                'reduced_field',
                ]

        if self.conditions_set:
            pre_full = self.get_conditions()
            pre = dict((k, pre_full[k]) for k in keys)
            self.conditions.update(pre)
        else:
            self.conditions_set = True

        self.conditions.update(kwargs)

        self.set_conditions_(**self.conditions)

    def get_density_total(self):
        """ Retuns a dictionary with the density totals. """

        totals = ['all_species',
                  'all_neutral',
                  'all_ion_positive',
                  'all_ion_negative',
                  'all_charge']

        data = self.get_density_total_()
        d = dict(zip(totals, data))
        return d

    def source_terms_matrix(self):
        """ Returns a matrix with reaction rates. """
        _, _, smatrix, _, _, _, _ = self.get_rates()

        return smatrix

    def get_rrt(self):
        """ Returns a matrix with reaction rates. """
        return self.mod.rrt

    def get_stech_matrix(self):
        reac_source_local = ones((self.N_REACTIONS,))
        return self.reac_source_matrix(reac_source_local).astype('i')

    def truncate_densities(self, epsilon=1e-10):
        """ Checks that densities are not too small.  If they are smaller than
        epsilon, they are set to epsilon.  """
        for s in self.species():
            dens = self.get_density(s)
            if dens < epsilon:
                self.set_density(s, 0.0, False)

    def print_densities(self):
        """ Outputs all the densities. """
        for s in self.species():
            print("%20s = %g cm^-3" % ('[%s]' % s, self.get_density(s)))

    def save_densities(self, fname):
        """ Save the densities to file fname in a format compatible with
        set_densities. """

        with open(fname, "w") as fp:
            for species in self.SPECIES:
                fp.write("%s  %g\n" % (species, self.get_density(species)))

    def load_densities(self, fname, fixed_dens=None):
        """ Sets the initial densities reading from file fname.
        Densities not specified in fname are set to 0.0. """
        init_dens = parse_densities(fname, allowed=self.species())

        if fixed_dens is None:
            fixed_dens = self.DEFAULT_FIXED_DENS

        for s in self.species():
            self.set_density(s,
                             init_dens.get(s, 0.0),
                             fixed_dens.get(s, False))
            print("%20s = %g cm^-3" % ('[%s]' % s, self.get_density(s)))

    def controlled_timestep(self, t, attempt_dt, max_dt):
        """ Attempts a timestep attempt_dt but only performs it if it smaller
        that max_dt.  In other case, divides attempt_dt into pieces smaller
        than max_dt and performs many timesteps.  """

        if attempt_dt < max_dt:
            self.timestep(t, attempt_dt)
        else:
            nsteps = int(attempt_dt / max_dt) + 1
            realized_dt = max_dt / nsteps

            for i in range(nsteps):
                self.timestep(t, realized_dt)


def parse_densities(fname, allowed=None):
    """ Reads densities from a file and returns a dictionary.  The file
    format must be
      SPECIES_NAME  INITIAL_VALUE # COMMENT
      # COMMENT
    """
    d = {}
    with open(fname) as fp:
        for iline, line in enumerate(fp):
            code = line.split('#')[0].strip()
            if not code:
                continue

            try:
                species, value = code.split()
            except ValueError:
                sys.stderr.write("%s:%d: %s\n" % (fname, iline, line))
                sys.stderr.write("Syntax error in the initialization file\n")
                sys.exit(-1)

            if allowed is not None and species not in allowed:
                warn("Species '%s' ignored" % species)

            d[species] = value

    return d
