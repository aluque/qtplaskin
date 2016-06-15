# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 23:47:41 2016

@author: erwan
"""

import numpy as np
from matplotlib.ticker import ScalarFormatter

class TimeFormatter(ScalarFormatter):
    
    def tformat(self,xp):
        
        dt=np.diff(self.axis.get_view_interval())

        nformat = '%.2f'        
        
        if dt<1e-7:
            xp = nformat %(xp*1e9)+'ns'
        elif dt<1e-4:
            xp = nformat %(xp*1e6)+'µs'
        elif dt<1e-1:
            xp = nformat %(xp*1e3)+'ms'
        return xp

    def pprint_val(self, x):
    
        xp = (x - self.offset) #/ (10. ** self.orderOfMagnitude)
        #if np.absolute(xp) < 1e-8:
        #    xp = 0
            
        xp = self.tformat(xp)            
            
        return xp

    def get_offset(self):
        """Return scientific notation, plus offset"""
        if len(self.locs) == 0:
            return ''
        s = ''
        if self.orderOfMagnitude or self.offset:
            offsetStr = ''
            if self.offset:
#                offsetStr = self.format_data(self.offset)=
                if np.abs(self.offset)<1e-7:
                    offsetStr = '%.2fns'%(self.offset*1e9)
                elif np.abs(self.offset)<1e-4:
                    offsetStr = '%.2fµs'%(self.offset*1e6)
                elif np.abs(self.offset)<1e-1:
                    offsetStr = '%.2fms'%(self.offset*1e3)
                if self.offset > 0:
                    offsetStr = '+' + offsetStr
            if self._useMathText:
                s = ''.join(('$', r'\mathdefault{', offsetStr, '}$'))
            elif self._usetex:
                s = '$%s$'%offsetStr
            else:
                s = offsetStr
            
        return self.fix_minus(s)

            