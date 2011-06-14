from distutils.core import setup
import matplotlib
try:
    import py2exe
except ImportError:
    pass

APP = ['main.py']
PY2APP_OPTIONS = {
    'argv_emulation': False,
    'semi_standalone': True,
    'includes': ['sip', 'PyQt4', 'PyQt4.QtCore', 'PyQt4.QtGui',
                 'matplotlib', 'numpy', 'scipy', 'h5py',
                 'h5py._objects', 'h5py.defs', 'h5py.utils',
                 'h5py._proxy'],
    'excludes': ['PyQt4.QtDesigner', 'PyQt4.QtNetwork',
                 'PyQt4.QtOpenGL', 'PyQt4.QtScript', 'PyQt4.QtSql',
                 'PyQt4.QtTest', 'PyQt4.QtWebKit', 'PyQt4.QtXml',
                 'PyQt4.phonon'],
    'resources': ['qtplaskin.svg'],
    'exclude_package_data': {'src':['*.c', '*.h',  '*.pyx', '*.pxd']}}
 

PY2EXE_OPTIONS = {
    "dll_excludes": ["MSVCP90.dll"],
    "includes": ["sip", "h5py.*"]}


setup(
    app=APP,
    options={'py2app': PY2APP_OPTIONS,
             'py2exe': PY2EXE_OPTIONS},
    windows=['main.py'],
    data_files=matplotlib.get_py2exe_datafiles())
