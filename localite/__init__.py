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
       
    def activate(self):
        self._send('{"current_instrument":"coil_' + self.id + '}')        
        return self._request('{"get":"current_instrument"}')[1]

    def request(self, msg:str):
        return self._client.request("coil_" + self.id + "_" + msg)
    
    def send(self, key:str, val:str):
        self._client.send('{"coil_' + self.id + '_' + key + '": ' + val + '}')        
    
    @property
    def id(self):
        return str(self._id)
    
    @id.setter
    def id(self, coil:int=0):
        if coil not in (0, 1):
            raise ValueError("Coil must be 0  or 1")
        self._id= coil
    
    @property
    def type(self):
        return self.request("type")
    
    @property
    def temperature(self):
        return self.request("temperature")
    
    @property
    def waveform(self):
        return self.request("waveform")
    
    @property
    def stimulator_mode(self):
        return self.request("stimulator_mode")
    
    @property
    def didt(self):
        return self.request("didt")
 
    @property
    def amplitude(self):
        return self.request("amplitude")
    
    @amplitude.setter
    def amplitude(self, amplitude:int):
        self.send("amplitude", str(amplitude))
        return self.request("amplitude")

    @property
    def target_index(self):
        return self.request("target_index")
  
    @target_index.setter
    def target_index(self, index:int):
        self.send("target_index", str(index))
        return self.request("target_index")
    
    @property
    def response(self):
        return self.request("response")
    
    @property
    def position(self):
        return self._request("response")
    
    def trigger(self):
        self._client.send('{"single_pulse":"COIL_' + str(self.id) + '"}')
    
    
# %%
# c.amplitude = 1        
# %timeit -n 1 -r 1000 c.trigger()
# %% 
class Localite():
    
    def __init__(self, coil:int=0, host:str="127.0.0.1", port:int=6666):
        self._client = Client(host=host, port=port)
        self.coil = coil              
        
    @property
    def coil(self):
        return self._coil
    
    @coil.setter
    def coil(self, coil:int=0):
        if coil not in (0, 1):
            raise ValueError("Coil must be 0  or 1")
        self._coil = Coil(coil=coil, host=self._client.host, 
                          port=self._client.port)
        
    @property
    def navigation_mode(self):
        return self._client.request("navigation_mode")
    
# %%