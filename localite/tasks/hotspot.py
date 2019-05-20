# -*- coding: utf-8 -*-
"""
Created on Fri May 17 12:37:26 2019

@author: Robert Guggenberger
"""
import localite
from localite import Response
from localite.tools import eeg_channels
import liesl
import time
import reiz

import matplotlib.pyplot as plt
# %%
coil = localite.Coil(host="134.2.117.173")
# %%
#from arduino.streamer import Streamer
#arduino = Streamer()
#patrick = liesl.open_streams(type='EEG', name="Spongebob-Data", hostname='Patrick')[0]
#marker = liesl.open_streams(type='Markers', name="serial_listener")[0]
#marker = liesl.open_streams(type='Markers', name="localite_marker")[0]

marker = liesl.open_streams(type='Markers',
                            name="BrainVision RDA Markers",
                            hostname='Patrick')[0]
bvr = liesl.open_streams(type='EEG',
                         name="BrainVision RDA",
                         hostname='Patrick')[0]

labels = liesl.inlet_to_chanidx(bvr)
emg_labels = [l for l in labels if l not in eeg_channels()]
eeg_labels = [l for l in labels if l in eeg_channels()]

buffer = liesl.RingBuffer(bvr, duration_in_ms=2000)
buffer.start()

        
def trigger(amplitude:int=20, pre_in_ms=25, post_in_ms= 50):
    coil.amplitude = amplitude
    onset_in_ms = coil.trigger()
    time.sleep(1)
    chunk, tstamps = buffer.get_timed()  
    response = Response(chunk=chunk,
                        tstamps=tstamps,
                        fs=buffer.fs, 
                        onset_in_ms=onset_in_ms)
    return response

def manual_trigger():
    triggered, onset_in_ms = marker.pull_sample()          
    onset_in_ms += marker.time_correction()
    print(triggered, onset_in_ms)
    #tpoint = arduino.wait_for('!')
    chunk, tstamps = buffer.get_timed()  
    print('[', end='')
    while tstamps[-1] < onset_in_ms +.25:
        print('.', end='')
        data, tstamps = buffer.get_timed()  
    print(']')
    
    response = Response(chunk=chunk,
                        tstamps=tstamps,
                        fs=buffer.fs, 
                        onset_in_ms=onset_in_ms)

    return response

def show(response, axes, emg_labels):    
    for ax, lbl in zip(axes.flatten(), emg_labels):
        ax.cla()    
        trace = response.get_trace(channel_idx=labels[lbl])
        vpp = response.get_vpp(channel_idx=labels[lbl])
        ax.plot(trace)
        textstr = 'Vpp = {0:3.2f}'.format(vpp)
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
        ax.set_title(lbl)
    plt.show()
    
    
def create_marker(response, coil, emg_labels):
    Vpp= {}
    for lbl in emg_labels:
        vpp = response.get_vpp(channel_idx=labels[lbl])
        Vpp[lbl] = vpp
    
    response_marker = {'amplitude':coil.amplitude, **coil.position, **Vpp}
    return response_marker
    
# %%
nr, nc = 2, len(emg_labels)//2
if len(emg_labels)%2: #uneven
    nc += 1   
fig, axes = plt.subplots(nrows=nr, ncols = nc, sharex=True, sharey=True)
fig.canvas.manager.window.move(-1280, 20)
fig.canvas.manager.window.resize(1280, 1024)
fig.tight_layout()
# %%
# response = trigger(0)    
# show(response, axes, emg_labels)
# time.sleep(5)
# %%
coil.amplitude = 40
counter = 0
while counter < 20:    
    plt.pause(0.5)
    print('Waiting for manual trigger')    
    response = manual_trigger()     
    response_marker = create_marker(response, coil, emg_labels)
    coil.push_dictionary(response_marker)
    show(response, axes, emg_labels)    
    plt.show()
    counter  += 1
    print(counter)
reiz.audio.Hertz().play()
