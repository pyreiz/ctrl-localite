#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 16 23:14:42 2019

@author: rgugg
"""

from localite.client import Client
# %% 
class Localite(Client):
    
    def __init__(self, coil=0, **kwargs):
        self.coil = coil
        super().__init__(**kwargs)
    
    
    def get_coil(self):
        return str(self._coil)
    
    def set_coil(self, coil:int=0):
        if coil not in (0, 1):
            raise ValueError("Coil must be 0  or 1")
        self._coil = coil
    
    coil = property(get_coil, set_coil)
    
    
    @property
    def coil_target_index(self):
        return self.request('{"get":"coil_' + self.coil + '_target_index"}')
        
    @property
    def coil_type(self):
        return self.request('{"get":"coil_'+ self.coil +'_type"}')
    
    @property
    def coil_temperature(self):
        return self.request('{"get":"coil_'+ self.coil +'_temperature"}')
    
# %%