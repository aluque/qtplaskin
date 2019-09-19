#! /usr/bin/env python 

"""
Launching script

Used to generate executable. Run::

    pip install pyinstaller
    pyinstaller cli.py
    
On Windows, this generates a cli.exe in qtplaskin\dist\cli. 
You may want to rename it to qtplaskin.exe 

Potential errors:

If "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 184:"
    see https://stackoverflow.com/questions/47692960/error-when-using-pyinstaller-unicodedecodeerror-utf-8-codec-cant-decode-byt    

"""

import qtplaskin
import sys

qtplaskin.main.main(sys.argv)
