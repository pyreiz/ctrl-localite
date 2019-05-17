#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 16 23:14:42 2019

@author: rgugg
"""

from localite.client import Client
# %%
class Coil():
    
    def __init__(self, coil=0, **kwargs):
        self.id = coil
        self._client = Client(**kwargs)
        self._send = self._client.send
        self._request = self._client.request
    
    
    def _get_id(self):
        return str(self._id)
    
    def _set_id(self, coil:int=0):
        if coil not in (0, 1):
            raise ValueError("Coil must be 0  or 1")
        self._id= coil
    
    id = property(_get_id, _set_id)
    
          
    @property
    def type(self):
        return self._request('{"get":"coil_'+ self.id +'_type"}')[1]
    
    @property
    def temperature(self):
        return self._request('{"get":"coil_'+ self.id +'_temperature"}')[1]
    
    @property
    def waveform(self):
        return self._request('{"get":"coil_'+ self.id +'_waveform"}')[1]
    
    @property
    def stimulator_mode(self):
        return self._request('{"get":"coil_'+ self.id +'_stimulator_mode"}')[1]
    
    @property
    def didt(self):
        return self._request('{"get":"coil_'+ self.id +'_didt"}')[1]
 

    def _get_amplitude(self):
        return self._request('{"get":"coil_'+ self.id +'_amplitude"}')[1]
    
    def _set_amplitude(self, amplitude:int):
        self._send('{"coil_' + self.id + '_amplitude": ' + str(amplitude) + '}')        
        return self._request('{"get":"coil_'+ self.id +'_amplitude"}')[1]

    amplitude = property(_get_amplitude, _set_amplitude)

    @property
    def _get_target_index(self):
        return self._request('{"get":"coil_' + self.id + '_target_index"}')[1]
  
    
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
    
    @property
    def coil_waveform(self):
        return self.request('{"get":"coil_'+ self.coil +'_waveform"}')
    
    @property
    def coil_stimulator_mode(self):
        return self.request('{"get":"coil_'+ self.coil +'_stimulator_mode"}')
    
    @property
    def coil_didt(self):
        return self.request('{"get":"coil_'+ self.coil +'_didt"}')
 
    @property
    def coil_amplitude(self):
        return self.request('{"get":"coil_'+ self.coil +'_amplitude"}')
    
    
    
# %%