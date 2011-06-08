import ConfigParser
import os.path

MY_PATH = os.path.split(__file__)[0]
config = ConfigParser.SafeConfigParser()
config.read(os.path.join(os.environ['HOME'], '.pyplaskinrc'))


ZDPLASKIN_EXEC_PATH = os.path.expanduser(config.get('zdplaskin', 'exec_path'))
ZDPLASKIN_LIB_PATH = os.path.expanduser(config.get('zdplaskin', 'lib_path'))

PYPLASKIN_SHARED_PATH = os.path.expanduser(config.get('pyplaskin',
                                                      'shared_path'))
