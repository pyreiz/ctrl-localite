# -*- coding: utf-8 -*-
'''Main structure for running TMS measurements'''


from localite.tasks.configure import Environment
import localite
from majel.majel import Majel
import liesl
# %%
env =  Environment()
env.coil = localite.Coil(host="134.2.117.173")
env.majel = Majel(log=env.coil.push_marker)
env.marker = liesl.open_streams(type='Markers',
                                name="BrainVision RDA Markers",
                                hostname='Patrick')[0]
env.bvr = liesl.open_streams(type='EEG',
                             name="BrainVision RDA",
                             hostname='Patrick')[0]
env.buffer = liesl.RingBuffer(env.bvr, duration_in_ms=2000)
env.setup()
channel_of_interest = 'EDC_L'
# %%        
from localite.tasks.generics import search_hotspot, find_highest
from localite.tasks.generics import measure_rmt
from localite.tasks.generics import free_mode
# %% Make a rough map for the hotspot  detection by applying several stimuli
collection = search_hotspot(trials=10, env=env)

try:    
    amp, pos, sorter  = find_highest(collection, channel=channel_of_interest)    
    env.majel.say('Höchste Antwort bei {0}. Stimulus mit {1} microVolt'.format(sorter[0]+1, amp[0]))    
    for ix in reversed(sorter):    
        print('Beim {0}. Stimulus Antwort {1}'.format(ix+1, collection[ix][channel_of_interest]))
except IndexError: #aborted run
    env.majel.say('Nicht genügend Durchläufe zur Auswertung')
# %% Fine tune the best hotspot by iterating over the best three
collection = []
for candidate in range(0,3,1):    
    candidate_collection = search_hotspot(trials=3, task_description='Ziel wechseln', env=env)
    collection.extend(candidate_collection)

try:
    amp, pos, sorter  = find_highest(collection, channel=channel_of_interest)
    env.majel.say('Höchste Antwort bei {0}. Stimulus mit {1} microVolt'.format(sorter[0]+1, amp[0]))
    for ix,_ in enumerate(collection):
        print('Beim {0}. Stimulus Antwort {1}'.format(ix+1, collection[ix][channel_of_interest]))   
except IndexError: #aborted run
    env.majel.say('Nicht genügend Durchläufe zur Auswertung')

#%% Bestimme die Ruhemotorschwellen
results = measure_rmt(channel=channel_of_interest,  threshold_in_uv=50, 
                      max_trials_per_amplitude=10, env=env)
#%%
free_mode(autotrigger=False, channel='EDC_L', env=env)




