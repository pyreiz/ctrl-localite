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
import random
from majel.majel import Majel
import matplotlib.pyplot as plt
from collections import defaultdict
# %%
coil = localite.Coil(host="134.2.117.173")
majel = Majel(log=coil.push_marker)
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
# %%        
def auto_trigger(amplitude:int=None):
    marker.pull_chunk() #flush the buffer
    if amplitude is not None:
        coil.amplitude = amplitude
    coil.trigger()
    triggered, onset_in_ms = marker.pull_sample()
    onset_in_ms += marker.time_correction()
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

def manual_trigger():
    marker.pull_chunk() #flush the buffer
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

def create_hotspot_canvas():
    nr, nc = 2, len(emg_labels)//2
    if len(emg_labels)%2: #uneven
        nc += 1   
    fig, axes = plt.subplots(nrows=nr, ncols = nc, sharex=True, sharey=True)
    fig.canvas.manager.window.move(-1280, 20)
    fig.canvas.manager.window.resize(1280, 1024)
    fig.tight_layout()
    return fig, axes

def create_rmt_canvas():
    fig, axes = plt.subplots(1,1)
    fig.canvas.manager.window.move(-1280, 20)
    fig.canvas.manager.window.resize(1280, 1024)
    fig.tight_layout()
    return fig, axes

def find_highest(collection, channel='EDC_L'):
    amp = 0
    amp_max = None
    pos_max = None
    for idx, r in enumerate(collection):        
        if r[channel]>amp:
            amp = amp
            amp_max  = idx
            pos_max = (r['x'], r['y'], r['z'])
    return amp_max, pos_max    
# %%
def search_hotspot(coil, automatic=True, trials=40, isi=(4,5)):
    fig, axes = create_hotspot_canvas()
    task_description = 'Starte {0} Hotspot-suche'.format(['manuelle','automatische'][automatic])
    majel.say(task_description)    
    start_confirmed = False    
    while coil.amplitude == 0:
        majel.say('Stelle eine Amplitude ein und bestätige')    
        response = manual_trigger()
    counter = 0
    collection = []
    while counter < trials:            
        if automatic and start_confirmed: 
            time.sleep(isi[0]+ (random.random()*(isi[1]-isi[0])))
            response = auto_trigger()     
        else:
            print('Waiting for manual trigger')    
            majel.say('Bereit')    
            response = manual_trigger()     
            start_confirmed = True
                    
        response_marker = create_marker(response, coil, emg_labels)
        coil.push_dictionary(response_marker)
        show(response, axes, emg_labels)    
        plt.show()
        plt.pause(0.5)        
        counter  += 1
        print(counter)        
        collection.append(response_marker)          
    return collection

def measure_rmt(coil, channel='EDC_L',  threshold_in_uv=50,
                max_trials_per_amplitude=10, isi=(4,5)):
    task_description = 'Starte Ruhemotorschwellenbestimmung'
    majel.say(task_description)     
    amplitude_response = defaultdict(list)    
    fig, ax = create_rmt_canvas()
    
    def show(response):
        ax.cla()    
        trace = response.get_trace(channel_idx=labels[channel])
        vpp = response.get_vpp(channel_idx=labels[channel])
        ax.plot(trace)
        textstr = 'Vpp = {0:3.2f}'.format(vpp)
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
        ax.set_title(channel)
        ax.set_xticks(range(response.pre_in_ms, response.post_in_ms, 5))        
                      
    while coil.amplitude == 0:
        majel.say('Stelle eine Amplitude ein und bestätige')    
        response = manual_trigger()
        
    automatic = False
    amplitude = coil.amplitude
    while True:        
        if not automatic:
            majel.say('Bereit')    
            response = manual_trigger()     
            automatic = True                            
        else:
            time.sleep(isi[0]+ (random.random()*(isi[1]-isi[0])))    
            response = auto_trigger() 
            
        amplitude = coil.amplitude        
        if amplitude == 0:
            majel.say('Durchgang beendet')            
            break
  
        # save result                         
        vpp = response.get_vpp(labels[channel])                
        amplitude_response[amplitude].append(vpp)    
               
        # analyse results
        vals = amplitude_response[amplitude]        
        above = [v>=threshold_in_uv for v in vals]
        cut_off = (max_trials_per_amplitude//2)
        above_rmt = sum(above) > cut_off 
        below_rmt = sum([not a for a in above]) > cut_off
        print(amplitude, vals)
        show(response)
        plt.pause(0.5)    
        # when more than max_trials, or any has sufficient counts, the state is reset
        # to start_confirmed, and requires manual setting
        if above_rmt or below_rmt: #also evaluates true if more than max_trials
            percent = sum(above)/len(above)
            majel.say('{0} schafft {1:2.0f} Prozent'.format(amplitude, percent*100))             
            automatic = False
        elif len(above) == max_trials_per_amplitude: #that means 50/50
            majel.say('{0} ist perfekt'.format(amplitude))
            automatic = False            
        
        for key in sorted(amplitude_response.keys()):
            vals = amplitude_response[key]
            print('{0} -> {1:3.2f} ({2})'.format(key, sum(vals)/len(vals), vals))
            
    return amplitude_response

# %%
collection = search_hotspot(coil, automatic=True, trials=10)
majel.say(f'Durchgang beendet')
index, pos = find_highest(collection, channel='EDC_L')
majel.say('Höchste Antwort bei {0}. Stimulus in {1:0.0f}, {2:0.0f}, und {3:0.0f}'.format(index+1, *pos))
# %%
results = measure_rmt(coil, channel='EDC_L',  threshold_in_uv=50, max_trials_per_amplitude=4, isi=(4,5))

