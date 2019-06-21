# -*- coding: utf-8 -*-
"""
Created on Mon May 20 17:40:27 2019

@author: AGNPT-M-001
"""

import matplotlib.pyplot as plt
from localite import Response
import time
import random
import reiz
from collections import defaultdict    
from localite.coil import Coil
from typing import NewType, Union
from liesl import RingBuffer
from pylsl import StreamInlet, FOREVER
from socket import timeout as TimeOutException
DataRingBuffer = NewType("DataRingBuffer", RingBuffer)
MarkerStreamInlet = NewType("MarkerStreamInlet", StreamInlet)
Seconds = Union[int,float]
import logging
logger = logging.getLogger(name=__file__)
# %%
def plot_trigger(coil:Coil,
                 marker:MarkerStreamInlet, 
                 buffer:DataRingBuffer,
                 auto:bool=False):
    coil.trigger() # trigger the coil
    _, onset_in_ms = marker.pull_sample()    # pull only the timestamp
    # pull_sample is blocking, so this waits until a trigger was received
    marker.pull_chunk() #flush the buffer of the marker stream
    chunk, tstamps = buffer.get_timed()           
    print('[', end='')
    while tstamps[-1] < onset_in_ms + .25:
        print('.', end='')
        chunk, tstamps = buffer.get_timed()    
    print(']')
    plt.cla()

    response = Response(chunk=chunk,
                        tstamps=tstamps,
                        fs=buffer.fs, 
                        onset_in_ms=onset_in_ms)
    plt.plot(response.get_trace(64))
   # response.remove_jitter()
    #plt.plot(response.get_trace(64))
    return response

def auto_trigger(coil:Coil,
                 marker:MarkerStreamInlet,
                 buffer:DataRingBuffer,
                 timeout:Seconds=1):    
    """Expect the TMS to be triggered manually    
    
    We wait a certain time for the  response to arrive. If this time has passed,
    we trigger again, assuming that somehow the TCP-IP command was lost in
    transition.
    """
    marker.pull_chunk() #flush the buffer to be sure we catch the latest sample  
    coil.trigger() #trigger the coil
    try:
        response = wait_for_trigger(coil, marker, buffer, timeout) #wait for the response
    except TimeOutException:
        logger.warning("Timeout,. repeating command to stimulate")
        response = auto_trigger(coil, marker, buffer, timeout)
    return response

def manual_trigger(coil:Coil,
                 marker:MarkerStreamInlet, 
                 buffer:DataRingBuffer):
    """Expect the TMS to be triggered manually
    
    We therefore also wait forever for the  response to arrive. If examiner
    becomes inpatient as the trigger was swallowed, a manual repetition is 
    necessary
    """
    
    marker.pull_chunk() #flush the buffer to be sure we catch the latest sample
    # wait  forever for the response, because
    response = wait_for_trigger(coil, marker, buffer, timeout=FOREVER) 
    
    return response

def wait_for_trigger(coil:Coil,
                    marker:MarkerStreamInlet, 
                    buffer:DataRingBuffer,
                    timeout:Seconds=1):    
    # pull the timestamp of the TMS pulse
    # pull_sample is blocking, so this waits until a trigger was received
    _, onset_in_ms = marker.pull_sample(timeout)
    if onset_in_ms is None:
        raise TimeOutException(f"Waited {timeout} for TMS pulse to arrive")
    chunk, tstamps = buffer.get_timed()  
    
    # wait a little bit longer to catch enough data around the TMS pulse
    print('[', end='')
    while tstamps[-1] < onset_in_ms +.25:
        print('.', end='')
        chunk, tstamps = buffer.get_timed() 
        time.sleep(0.05)
    print(']')
    
    # create and return the response
    response = Response(chunk=chunk,
                        tstamps=tstamps,
                        fs=buffer.fs, 
                        onset_in_ms=onset_in_ms)
    return response
    
def create_marker(response, coil, emg_labels, labels):
    amplitude, position = coil.amplitude, coil.position
    Vpp= {}
    for lbl in emg_labels:
        vpp = response.get_vpp(channel_idx=labels[lbl])
        Vpp[lbl] = vpp        

    if position is None:
        reiz.audio.library.dong.play()         
        response_marker = {'amplitude':amplitude, 'x':None, 'y': None, 'z':None, **Vpp}
    else:
        response_marker = {'amplitude':amplitude, **position, **Vpp}
        
    return response_marker

def find_highest(collection, channel='EDC_L'):
    vals = [r[channel] for r in collection]
    shuffler = list(reversed(sorted(range(len(vals)),key=vals.__getitem__)))
    amps = [vals[s] for s in shuffler]
    pos = [(collection[s]['x'], collection[s]['y'], collection[s]['z']) for s in shuffler]
    return amps, pos, shuffler
# %%
def search_hotspot(trials=40, isi=(3.5,4.5),
                   task_description='Starte Hotspotsuche',
                   env=None,
                   run_automatic:bool=False):
    print(__file__)
    coil = env.coil
    majel = env.majel
    labels = env.labels
    emg_labels = env.emg_labels
    marker, buffer = env.marker, env.buffer
    
    plt.close('all')
    def create_hotspot_canvas(emg_labels):
        nr, nc = 2, len(emg_labels)//2
        if len(emg_labels)%2: #uneven
            nc += 1   
        fig, axes = plt.subplots(nrows=nr, ncols = nc, sharex=True, sharey=True)
        fig.canvas.manager.window.move(-1280, 20)
        fig.canvas.manager.window.resize(1280, 1024)
        fig.tight_layout()
        return fig, axes

    fig, axes = create_hotspot_canvas(emg_labels)
    def show(response, axes, emg_labels, labels):    
        xticks, xticklabels, xlim = response.get_xaxis(stepsize=25)        
        for ax, lbl in zip(axes.flatten(), emg_labels):
            ax.cla()    
            trace = response.get_trace(channel_idx=labels[lbl])
            vpp = response.get_vpp(channel_idx=labels[lbl])
            ax.plot(trace)
            for pos, val in zip(response.peakpos_in_ms, response.peakval):
                ax.plot([pos, pos],[0, val], color='red', linestyle=':')
            ax.plot([response.pre_in_ms, response.pre_in_ms],[-100, 100], color='red')
            textstr = 'Vpp = {0:3.2f}'.format(vpp)
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
                    verticalalignment='top', bbox=props)
            ax.set_title(lbl)            
            ax.set_xticks(xticks)
            ax.set_xlim(xlim)
            ax.set_xticklabels(xticklabels)
 
        plt.show()
    
    majel.say(task_description)    
    
    if coil.amplitude == 0:
        majel.say('Stelle eine Amplitude ein und bestätige')    
        response = manual_trigger(coil, marker, buffer)
        
    counter = 0
    collection = []
    automatic = False    
    while counter < trials:
        if automatic: 
            print('Automatic trigger')    
            time.sleep(isi[0]+ (random.random()*(isi[1]-isi[0])))
            response = auto_trigger(coil, marker, buffer)
        else:           
            print('Waiting for manual trigger')    
            majel.say('Bereit')    
            response = manual_trigger(coil, marker, buffer)                
            if run_automatic:
                automatic = True
                
        if coil.amplitude == 0:
            break
        
        response_marker = create_marker(response, coil, emg_labels, labels)
        coil.set_response(response, 
                          channel_idx=env.labels[env.channel_of_interest])
        coil.push_dictionary(response_marker)
        show(response, axes, emg_labels, labels)                          
        props = dict(boxstyle='round', facecolor='white', alpha=1)
        counter  += 1
        ax = axes[0,0]
        ax.text(-.15, 1.05, f'{counter} of {trials}', transform=ax.transAxes, fontsize=14,
                verticalalignment='top', bbox=props)   

        plt.pause(0.5)                    
        collection.append(response_marker)         
           
    majel.say(f'Durchgang beendet')
    return collection
# %%
def measure_rmt(channel='EDC_L',  threshold_in_uv=50,
                max_trials_per_amplitude=10, isi=(3.5,4.5),
                task_description = 'Starte Ruhemotorschwelle',
                env=None):    
   
    labels = env.labels
    coil = env.coil
    majel, marker, buffer = env.majel, env.marker, env.buffer
    
    plt.close('all')        
    def create_rmt_canvas():
        fig, axes = plt.subplots(1,1)
        fig.canvas.manager.window.move(-1280, 20)
        fig.canvas.manager.window.resize(1280, 1024)
        fig.tight_layout()
        return fig, axes

    fig, ax = create_rmt_canvas()    
    def show(response, labels):
        ax.cla()    
        trace = response.get_trace(channel_idx=labels[channel])
        vpp = response.get_vpp(channel_idx=labels[channel])
        ax.plot(trace)
        ax.plot([response.pre_in_ms, response.pre_in_ms],[-100, 100], color='red')
        for pos, val in zip(response.peakpos_in_ms, response.peakval):
            ax.plot([pos, pos],[0, val], color='red', linestyle=':')
        textstr = 'Vpp = {0:3.2f}'.format(vpp)
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
        ax.set_title(channel)
        xticks, xticklabels, xlim = response.get_xaxis()
        ax.set_xticks(xticks)
        ax.set_xlim(xlim)
        ax.set_xticklabels(xticklabels)
                          
    majel.say(task_description)         
    
    if coil.amplitude == 0:
        majel.say('Stelle eine Amplitude ein und bestätige')    
        response = manual_trigger(coil, marker, buffer)     
        
    amplitude_response = defaultdict(list)        
    amplitude = coil.amplitude
    automatic = False
    while True:        
        if not automatic:          
            majel.say('Bereit')    
            response = manual_trigger(coil, marker, buffer)     
            automatic = True                            
        else:
            time.sleep(isi[0]+ (random.random()*(isi[1]-isi[0])))    
            response = auto_trigger(coil, marker, buffer)     
            
        amplitude = coil.amplitude        
        if amplitude == 0:      
            break
  
        # show and save result  
        coil.set_response(response, channel_idx=env.labels[channel])
        vpp = response.get_vpp(labels[channel])                
        amplitude_response[amplitude].append(vpp)    
        show(response, labels)
        count = len(amplitude_response[amplitude])
        props = dict(boxstyle='round', facecolor='white', alpha=1)        
        ax.text(-.025, 1, f'#{count} at {amplitude}%', transform=ax.transAxes, fontsize=14,
                verticalalignment='top', bbox=props)     
        # analyse results
        vals = amplitude_response[amplitude]        
        above = [v>=threshold_in_uv for v in vals]
        cut_off = (max_trials_per_amplitude//2)
        above_rmt = sum(above) > cut_off 
        below_rmt = sum([not a for a in above]) > cut_off
        
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
            
    majel.say(f'Durchgang beendet')            
    return amplitude_response

# %%
def free_mode(autotrigger=5, channel='EDC_L', isi=(3.5,4.5),
              task_description = 'Starte freien Modus',
              env=None):    
    labels = env.labels
    coil = env.coil
    majel, marker, buffer = env.majel, env.marker, env.buffer
    
    plt.close('all')        
    def create_canvas():
        fig, axes = plt.subplots(1,1)
        fig.canvas.manager.window.move(-1280, 20)
        fig.canvas.manager.window.resize(1280, 1024)
        fig.tight_layout()
        return fig, axes

    fig, ax = create_canvas()    
    def show(response, labels):
        ax.cla()    
        trace = response.get_trace(channel_idx=labels[channel])
        vpp = response.get_vpp(channel_idx=labels[channel])
        ax.plot(trace)
        ax.plot([response.pre_in_ms, response.pre_in_ms],[-100, 100], color='red')
        for pos, val in zip(response.peakpos_in_ms, response.peakval):
            ax.plot([pos, pos],[0, val], color='red', linestyle=':')
            
        textstr = 'Vpp = {0:3.2f}'.format(vpp)
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
        ax.set_title(channel)
        xticks, xticklabels, xlim = response.get_xaxis()
        ax.set_xticks(xticks)
        ax.set_xlim(xlim)
        ax.set_xticklabels(xticklabels)
                          
    majel.say(task_description)         
    
    if coil.amplitude == 0:
        majel.say('Stelle eine Amplitude ein und bestätige')    
        response = manual_trigger(coil, marker, buffer)     
            
    automatic = False
    tix_counts = defaultdict(list)    
    if not autotrigger:
        majel.say('Bereit')
    while True:        
        if not automatic:          
            if autotrigger:
                majel.say('Bereit')    
            response = manual_trigger(coil, marker, buffer)     
            if autotrigger:
                automatic = True                  
        else:
            time.sleep(isi[0]+ (random.random()*(isi[1]-isi[0])))    
            response = auto_trigger(coil, marker, buffer)     

        # show result                                             
        coil.set_response(response, channel_idx=env.labels[channel])
        show(response, labels)        
        # count up
        tix = coil.target_index
        count = tix_counts.get(tix, 0)
        count += 1
        tix_counts[tix] = count
        if count >= autotrigger:
            automatic = False
        # and show        
        props = dict(boxstyle='round', facecolor='white', alpha=1)
        ax.text(-.025, 1, f'#{count} at {tix}', transform=ax.transAxes, fontsize=14,
                verticalalignment='top', bbox=props)   
        plt.pause(0.01)
        
        amplitude = coil.amplitude        
        if amplitude == 0:       
            break
        
    majel.say(f'Durchgang beendet')
