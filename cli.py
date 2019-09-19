#! /usr/bin/env python 

"""
Launching script

Used to generate executable. Run::

    pip install pyinstaller
    pyinstaller cli.py 

"""

import qtplaskin
import sys

qtplaskin.main.main(sys.argv)
