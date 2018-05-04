# -*- coding: utf-8 -*-
"""
How to use?

ZdPlaskin output files are not embedded in QtPlaskin, as they are very heavy

You need to generate a first set of output files. Just run whatever case you 
have available

Then place it in a Results/ folder in qtplaskin/test

Dont forget never to git these files 
"""

import qtplaskin

qtplaskin.main.load('./Results')
