#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 16 23:14:42 2019

@author: rgugg
"""

from localite.client import SmartClient
# %%
class Coil():
    
    def __init__(self, coil=0, **kwargs):
        self.id = coil
        self._client = SmartClient.get_running_instance(**kwargs)
       
    def request(self, msg:str):
        return self._client.request("coil_" + self.id + "_" + msg)
    
    def send(self, key:str, val:str):
        self._client.send('{"coil_' + self.id + '_' + key + '": ' + val + '}')        
    
    def activate(self):
        self._client.send('{"current_instrument":"COIL_' + self.id +'"}')
    
    def trigger(self):
        self._client.trigger(self.id)
    
    
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
    def position(self):
        return self.request("position")
        
    @property
    def position_reached(self):
        return True if self.request("position_control") == "TRUE" else False
    
    @property
    def status(self):
        return self.request("status")
    
    @property
    def response(self):
        return self.request("response")
    
# %%
# c.amplitude = 1        
# %timeit -n 1 -r 1000 c.trigger()