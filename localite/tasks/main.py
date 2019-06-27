# -*- coding: utf-8 -*-
'''Main structure for running TMS measurements'''


from localite.tasks.configure import Environment
import localite
from majel.majel import Majel
import liesl
from liesl import localhostname
from liesl.files.session import Recorder, Session
from reiz import clock
# %%
env =  Environment()
env.coil = localite.Coil(host="134.2.117.173")
env.majel = Majel(log=env.coil.push_marker)
env.marker = liesl.get_stream_matching(type='Markers',
                                       name="BrainVision RDA Markers",
                                       hostname=localhostname)

env.bvr = liesl.get_streaminfo_matching(type='EEG',
                                        name="BrainVision RDA",
                                        hostname=localhostname)

env.buffer = liesl.RingBuffer(env.bvr, duration_in_ms=2000)
env.channel_of_interest  = 'EDC_R'
env.setup()

streamargs = [{'name':"localite_marker", "hostname": localhostname},
              {'name':"reiz_marker_sa", "hostname": localhostname},
              {'name':"BrainVision RDA Markers", "hostname": localhostname},
              {'name':"BrainVision RDA", "hostname": localhostname}]

session = Session(prefix="VvNn", 
                  recorder=Recorder(path_to_cmd=r"~/Desktop/LabRecorder.lnk"),
                  streamargs=streamargs)

# %%        
from localite.tasks.generics import search_hotspot, find_highest
from localite.tasks.generics import measure_rmt
from localite.tasks.generics import free_mode
# %% Make a rough map for the hotspot  detection by applying several stimuli
with session("hotspot-detection"):
    collection = search_hotspot(trials=40, env=env)

try:    
    amp, pos, sorter  = find_highest(collection, channel=env.channel_of_interest)    
    #env.majel.say('Höchste Antwort bei {0}. Stimulus mit {1} microVolt'.format(sorter[0]+1, amp[0]))    
    for ix in reversed(sorter):    
        print('Beim {0}. Stimulus Antwort {1}'.format(ix+1, collection[ix][env.channel_of_interest]))
except IndexError as e: #aborted run
    env.majel.say('Nicht genügend Durchläufe zur Auswertung' + str(e))
# %% Fine tune the best hotspot by iterating over the best three
with session("hotspot-iteration"):
    collection = []
    for candidate in range(0,3,1):    
        candidate_collection = search_hotspot(trials=3, task_description='Ziel wechseln', env=env)
        collection.extend(candidate_collection)
    env.majel.say('Fertig')
    clock.sleep(2)
try:
    amp, pos, sorter  = find_highest(collection, channel=env.channel_of_interest)
    #env.majel.say('Höchste Antwort bei {0}. Stimulus mit {1} microVolt'.format(sorter[0]+1, amp[0]))
    for ix,_ in enumerate(collection):
        print('Beim {0}. Stimulus Antwort {1}'.format(ix+1, collection[ix][env.channel_of_interest]))   
except IndexError: #aborted run
    env.majel.say('Nicht genügend Durchläufe zur Auswertung')

#%% Bestimme die Ruhemotorschwellen
with session("measure-rmt"):
    results = measure_rmt(channel=env.channel_of_interest,  threshold_in_uv=50, 
                          max_trials_per_amplitude=10, env=env)
#%% Mapping - should be done manually
with session("mapping"):
    free_mode(autotrigger=5, channel='EDC_L', env=env)





