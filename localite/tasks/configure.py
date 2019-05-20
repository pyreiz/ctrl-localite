# -*- coding: utf-8 -*-
"""
Created on Mon May 20 18:07:24 2019

@author: AGNPT-M-001
"""

# %%
import liesl
from dataclasses import dataclass
from majel.majel import Majel
from localite.tools import eeg_channels
import localite
@dataclass
class Environment():
    coil = localite.Coil(host="134.2.117.173")
    majel = Majel(log=coil.push_marker)
    marker = liesl.open_streams(type='Markers',
                                name="BrainVision RDA Markers",
                                hostname='Patrick')[0]
    bvr = liesl.open_streams(type='EEG',
                             name="BrainVision RDA",
                             hostname='Patrick')[0]
    
    buffer = liesl.RingBuffer(bvr, duration_in_ms=2000)
    
    def setup(self):
        self.buffer.start()
        self.labels = liesl.inlet_to_chanidx(self.bvr)
        self.emg_labels = [l for l in self.labels if l not in eeg_channels()]
        self.eeg_labels = [l for l in self.labels if l in eeg_channels()]    