# -*- coding: utf-8 -*-
"""
Created on Fri May 17 12:37:26 2019

@author: Robert Guggenberger
"""
import localite
from localite.tools import eeg_channels
import liesl
import time
import matplotlib.pyplot as plt
# %%
coil = localite.Coil(host="134.2.117.173")
#patrick = liesl.open_streams(type='EEG', name="Spongebob-Data", hostname='Patrick')[0]
bvr = liesl.open_streams(type='EEG', name="BrainVision RDA", hostname='Patrick')[0]
labels = liesl.inlet_to_chanidx(bvr)
emg_labels = [l for l in labels if l not in eeg_channels()]
eeg_labels = [l for l in labels if l in eeg_channels()]

buffer = liesl.RingBuffer(bvr, duration_in_ms=2000)
buffer.start()
# %%
def trigger(amplitude:int=20):
    coil.amplitude = amplitude
    tpoint = coil.trigger()
    time.sleep(1)
    data, tstamps = buffer.get_timed()  
    onset = (tstamps>tpoint)[:,0].argmax()    
    data = data[onset-50:onset+100,:]    
    return data
    
def show(response, axes, emg_labels):
    for ax, lbl in zip(axes.flatten(), emg_labels):
        ax.cla()
        data = response[50:, labels[lbl]]
        Vpp = data.max()-data.min()
        ax.plot(data)
        textstr = 'Vpp = {0:3.2f}'.format(Vpp)
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
        ax.set_title(lbl)

# %%
nr, nc = 2, len(emg_labels)//2
if len(emg_labels)%2: #uneven
    nc += 1
   
fig, axes = plt.subplots(nrows=nr, ncols = nc, sharex=True, sharey=True)
fig.canvas.manager.window.move(-1280, 20)
fig.canvas.manager.window.resize(1280, 1024)
fig.tight_layout()
# %%
response = trigger(20)    
show(response, axes, emg_labels)