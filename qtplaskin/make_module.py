#!/usr/bin/env python

from argparse import ArgumentParser
from subprocess import call, Popen, PIPE
from string import Template
import os
from warnings import warn
import sys
import shutil

import re

# Read global config
from qtplaskin import config


def preprocessor(infile, outfile='.'):
    p = Popen(os.path.join(config.ZDPLASKIN_EXEC_PATH, 'preprocessor'),
              shell=True, stdin=PIPE)
    p.communicate("%s\n%s\n\n" % (infile, outfile))

re_sep = re.compile(r',\s*')
re_assign = re.compile(r'\s*([a-zA-Z0-9_]+)\s*=\s*(\S+)')

bolsig_lib = {'darwin': 'bolsig_x86_64.dylib',
              'linux2': 'bolsig_x86_64.so'}


def find_params(fortran_file):
    d = {}
    with open(fortran_file) as fin:
        for line in iter_joined_lines(fin):
            try:
                indx = line.index('::')
            except ValueError:
                continue

            assignments = re_sep.split(line[indx + 2:])
            for a in assignments:
                m = re_assign.match(a)
                if m:
                    d[m.group(1)] = m.group(2)
    return d


def fill_template(module, fortran_file, out_file,
                  template=os.path.join(config.PYPLASKIN_SHARED_PATH,
                                        'template.pyf')):
    params = find_params(fortran_file)
    params['module_name'] = module

    with open(template) as ftempl:
        templ = Template(ftempl.read())

    with open(out_file, 'w') as fout:
        fout.write(templ.safe_substitute(params))


def iter_joined_lines(line_iterator):
    current = ''
    for line in line_iterator:
        sline = line.rstrip()
        if sline[-1] == '&':
            current = current + sline[:-1]
        else:
            yield current + sline
            current = ''


def create_dvode_m():
    """ Creates the dvode_f90_m.mod if it does not exist. """
    target = os.path.join(config.ZDPLASKIN_EXEC_PATH, 'dvode_f90_m.mod')
    if os.path.exists(target):
        # It exists already.  We copy it to our current dir
        shutil.copyfile(target, 'dvode_f90_m.mod')
        return

    source = os.path.join(config.ZDPLASKIN_EXEC_PATH, 'dvode_f90_m.F90')
    o_file = os.path.join(config.ZDPLASKIN_EXEC_PATH, 'dvode_f90_m.o')
    cmd = "gfortran -c %s -o %s" % (source, o_file)

    call(cmd, shell=True)

    # We move it to an accessible place for next time
    shutil.copyfile('dvode_f90_m.mod', target)


def f2py(module, pyf_file, fortran_file, bolsig=None):
    os.environ["NO_SCIPY_IMPORT"] = "f2py"
    from numpy.f2py import main as f2py_main

    if bolsig is None:
        bolsig = os.path.join(config.ZDPLASKIN_LIB_PATH,
                              bolsig_lib[sys.platform])

    # In Mac OS X, f2py expects a .so file but shared libraries have a .dylib
    # We simply copy the .dylib to a .so
    if sys.platform == 'darwin':
        base, ext = os.path.splitext(bolsig)
        so_file = '.'.join([base, 'so'])
        shutil.copyfile(bolsig, so_file)
        bolsig = so_file

    create_dvode_m()

    args = ("f2py -m %s -c --opt=\"-O3\" %s %s %s %s --fcompiler=gnu95"
            % (module, pyf_file, fortran_file,
               os.path.join(config.ZDPLASKIN_EXEC_PATH, 'dvode_f90_m.F90'),
               bolsig)).split()

    print(args)

    sys.argv = args
    f2py_main()

    # In Mac OS X, some versions of python want a .dylib file for the module
    if sys.platform == 'darwin':
        dylib_file = '.'.join([module, 'dylib'])
        so_file = '.'.join([module, 'so'])

        os.remove(dylib_file)
        os.symlink(so_file, dylib_file)


def cleanup():
    """ If some files exist, they can cause problems in the compilation.
    """
    remove_files = ['zdplaskin.mod']
    for f in remove_files:
        print("Removing %s" % f)
        try:
            os.remove(f)
        except OSError:
            pass


def main():
    parser = ArgumentParser()
    (opts, args) = parser.parse_args()

    for inp in args:
        base, ext = os.path.splitext(inp)
        # Many programs get confused about dots in the basename
        base = base.replace('.', '_')

        if ext != '.inp':
            warn("Extension of %s is not .inp" % inp)

        fortran_file = base + '_m.F90'
        pyf_file = base + '.pyf'

        cleanup()
        preprocessor(inp, outfile=fortran_file)
        fill_template(base, fortran_file, pyf_file)
        f2py(base, pyf_file, fortran_file)


if __name__ == "__main__":
    main()
