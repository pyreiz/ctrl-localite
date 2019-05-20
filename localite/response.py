# -*- coding: utf-8 -*-
"""
Created on Mon May 20 10:41:04 2019

@author: AGNPT-M-001
"""
from dataclasses import dataclass
# %%
@dataclass
class Response():
    from numpy import ndarray
    chunk:ndarray
    tstamps:ndarray
    fs:int = 1000
    pre_in_ms:float = 25
    post_in_ms:float = 75
    onset_in_ms:float=None
        
    @property
    def onset(self):
        return (self.tstamps>self.onset_in_ms)[:,0].argmax()

    @property
    def pre(self):
        pre = int(self.pre_in_ms*1000/self.fs)
        return self.onset-pre

    @property
    def post(self):
        post = int(self.post_in_ms*1000/self.fs)
        return self.onset+post

    def get_trace(self, channel_idx:int=0):
        bl = self.chunk[self.pre:self.onset, channel_idx]        
        response = self.chunk[self.onset:self.post, channel_idx].copy()     
        response -= bl.mean()
        return response
    
    def get_vpp(self, channel_idx:int=0):        
        data = self.chunk[self.onset:self.post, channel_idx]                
        return data.max()-data.min()