# -*- coding: utf-8 -*-
"""
Created on Fri May 17 13:49:12 2019

@author: AGNPT-M-001
"""

def eeg_channels():
    import os
    LIBPATH = os.path.dirname(os.path.realpath(__file__))
    LIBPATH = LIBPATH.split(os.path.sep + 'localite')[0]    
    fname = os.path.join(LIBPATH, 'lib', 'standard_1005.elc')
    lines = []
    start = False
    with open(fname) as f:   
        for line in f:
            if not start and 'Labels\n' in line:
                start = True
            else:
                lines.append(line.strip())

    return lines