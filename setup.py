import sys
from distutils.core import setup
#from setuptools import setup
import shutil
from subprocess import call

import matplotlib
try:
    import py2exe
except ImportError:
    pass

APP = ['qtplaskin.py']
PY2APP_OPTIONS = {
    'iconfile': 'qtplaskin3.icns',
    'argv_emulation': False,
    'semi_standalone': False,
    # 'strip': False,
    'includes': ['sip', 'PyQt4',
                 'PyQt4.QtCore', 'PyQt4.QtGui',
                 #'PyQt4.QtXml', #'PyQt4.QtMultimedia',
                 'matplotlib', 'numpy', 'scipy', 'h5py',
                 'h5py._objects', 'h5py.defs', 'h5py.utils',
                 'h5py._proxy'],
    'frameworks': ['/opt/local/share/qt4/plugins/imageformats/libqgif.dylib',],
    'excludes': ['libQtGui.4.dylib', 'libQtGui.4.dylib'],
    
    #              'PyQt4.QtDesigner', 'PyQt4.QtNetwork',
    #              'PyQt4.QtOpenGL', 'PyQt4.QtScript', 'PyQt4.QtSql',
    #              'PyQt4.QtTest', 'PyQt4.QtWebKit', 'PyQt4.QtXml',
    #              'PyQt4.phonon'],
    'resources': ['qtplaskin3.png',
                  '/opt/local/lib/Resources/qt_menu.nib',
                  'modeldata.py', 'mainwindow.py', 'zdplaskin.py',
                  'runner.py', 'mplwidget.py'],
    }
 
# 'exclude_package_data': {'src':['*.c', '*.h',  '*.pyx', '*.pxd']}
PY2EXE_OPTIONS = {
    "dll_excludes": ["MSVCP90.dll"],
    "includes": ["sip", "h5py.*"]}

shutil.rmtree('dist', ignore_errors=True)

if sys.argv[1] == 'py2exe':
    from distutils.core import setup
    setup(
        app=APP,
        options={'py2app': PY2APP_OPTIONS,
                 'py2exe': PY2EXE_OPTIONS},
        windows=['qtplaskin.py'],
        setup_requires=['py2app'],
        data_files=matplotlib.get_py2exe_datafiles())
    shutil.move('dist', 'qtplaskin-win')
    call("zip qtplaskin-win.zip qtplaskin-win/*", shell=True)
    


elif sys.argv[1] == 'py2app':
    from setuptools import setup
    setup(
        name="QtPlaskin",
        version="0.2",
        app=APP,
        options={'py2app': PY2APP_OPTIONS,
                 'py2exe': PY2EXE_OPTIONS},
        data_files=matplotlib.get_py2exe_datafiles())

    # py2app does not handle plugins correctly, so we copy them manually

    # Be careful with the absolute paths here.  They may change.
    shutil.copytree("/opt/local/share/qt4/plugins",
                    "dist/qtplaskin.app/Contents/MacOS/plugins")
    shutil.copy("qt.conf", "dist/qtplaskin.app/Contents/Resources/")
    shutil.copy("README", "dist/README.txt")
    call("hdiutil create QtPlaskin.dmg -ov -srcfolder dist/", shell=True)
