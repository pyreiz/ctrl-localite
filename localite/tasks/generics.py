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
    
# %%
def plot_trigger(coil, marker, buffer, auto=False):    
    coil.trigger()
    triggered, onset_in_ms = marker.pull_sample()    
    marker.pull_chunk() #flush the buffer
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

def auto_trigger(coil, marker, buffer):    
    marker.pull_chunk() #flush the buffer  
    coil.trigger()
    return wait_for_trigger(coil, marker, buffer)

def manual_trigger(coil, marker, buffer):
    marker.pull_chunk() #flush the buffer  
    return wait_for_trigger(coil, marker, buffer)

def wait_for_trigger(coil, marker, buffer):    
    triggered, onset_in_ms = marker.pull_sample()                 
    chunk, tstamps = buffer.get_timed()  
    print('[', end='')
    while tstamps[-1] < onset_in_ms +.25:
        print('.', end='')
        chunk, tstamps = buffer.get_timed() 
        time.sleep(0.05)
    print(']')
    
    response = Response(chunk=chunk,
                        tstamps=tstamps,
                        fs=buffer.fs, 
                        onset_in_ms=onset_in_ms)
    return response
    
def create_marker(response, coil, emg_labels, labels):
    amplitude, position = coil.amplitude, coil.position
    if position is None:
        reiz.audio.library.dong.play()         
        return None
    else:
        Vpp= {}
        for lbl in emg_labels:
            vpp = response.get_vpp(channel_idx=labels[lbl])
            Vpp[lbl] = vpp        
        response_marker = {'amplitude':amplitude, **position, **Vpp}
        return response_marker

def find_highest(collection, channel='EDC_L'):
    vals = [r[channel] for r in collection]
    shuffler = list(reversed(sorted(range(len(vals)),key=vals.__getitem__)))
    amps = [vals[s] for s in shuffler]
    pos = [(collection[s]['x'], collection[s]['y'], collection[s]['z']) for s in shuffler]
    return amps, pos, shuffler
# %%
def search_hotspot(trials=40, isi=(2,3),
                   task_description='Starte Hotspotsuche',
                   env=None):
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
            automatic = True
        if coil.amplitude == 0:
            break
        
        response_marker = create_marker(response, coil, emg_labels, labels)
        if not response_marker:
            print('Position sensors blocked, skipping')
        else:
            coil.push_dictionary(response_marker)
            show(response, axes, emg_labels, labels)                          
            props = dict(boxstyle='round', facecolor='white', alpha=1)
            ax = axes[0,0]
            ax.text(-.15, 1.05, f'{counter} of {trials}', transform=ax.transAxes, fontsize=14,
                    verticalalignment='top', bbox=props)   

            plt.pause(0.5)        
            counter  += 1
            print(counter)        
            collection.append(response_marker)         
            
    return collection
# %%
def measure_rmt(channel='EDC_L',  threshold_in_uv=50,
                max_trials_per_amplitude=10, isi=(2,3),
                task_description = 'Starte Ruhemotorschwelle',
                env=None):    
    from collections import defaultdict    
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
            majel.say('Durchgang beendet')            
            break
  
        # show and save result                         
        vpp = response.get_vpp(labels[channel])                
        amplitude_response[amplitude].append(vpp)    
        show(response, labels)
        
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
    return amplitude_response

# %%
def free_mode(autotrigger=True, channel='EDC_L', isi=(2,3),
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
            
    amplitude = coil.amplitude
    automatic = not autotrigger
    while True:        
        if not automatic:          
            majel.say('Bereit')    
            response = manual_trigger(coil, marker, buffer)     
            automatic = autotrigger                  
        else:
            time.sleep(isi[0]+ (random.random()*(isi[1]-isi[0])))    
            response = auto_trigger(coil, marker, buffer)     
            
        amplitude = coil.amplitude        
        if amplitude == 0:
            majel.say('Durchgang beendet')            
            break
  
        # show result                                 
        show(response, labels)
        plt.pause(0.5)  
# %%
def mapping(channel='EDC_L', trials_per_position=3, isi=(2,3),
            task_description = 'Starte Mapping',
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
                
    keep_target = False
    counter = 0   
    target_idx = 0
    coil.target_index = target_idx  
    while True:        
        if not keep_target:          
            majel.say('Ziel wechseln')    
            while not coil.position_reached:
                pass
            else:
                response = auto_trigger(coil, marker, buffer)     
                keep_target = True
                counter  += 1
        else:
            while not coil.position_reached:
                pass
            else:
               response = auto_trigger(coil, marker, buffer)     
               counter  += 1
        
        if counter == trials_per_position:
            keep_target = False
            target_idx += 1
            coil.target_index = target_idx         
        if coil.amplitude  == 0 or coil.target_index != target_idx:
            majel.say('Durchgang beendet')            
            break
  
        # show result                                 
        show(response, labels)
        plt.pause(0.5)    
     