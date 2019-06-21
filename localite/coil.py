#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""User-interface to control the TMS coil via LocaliteJSON

@author: Robert Guggenberger
"""

from localite.client import SmartClient
from json import dumps as _dumps
# %%
class Coil():
    """Coil is a user-friendly interface to control the TMS and Localite

    during instantiation, it opens an LSL-Marker-StreamOutlet which runs in the 
    background, continously reads the TCP-IP messages sent from localite, and
    forwards whenever a stimulus was applied. Additionally, you can forward
    your own markers using `~.push_marker` or `~.push_dictionary`

    it wraps a SmartClient, and processes Responses
    """
    def __init__(self, coil:int=0, **kwargs):
        self.id = coil
        self._client = SmartClient.get_running_instance(**kwargs)

    def push_dictionary(self, marker:dict):
        "json encodes a dictionary before pushing it with `~.push_marker`"
        self._client.push_marker(_dumps(marker))   
        
    def push_marker(self, marker:str):
        "pushes a str to the Marker-Stream running in the background"
        self._client.push_marker(marker)
        
    def request(self, msg:str):
        return self._client.request("coil_" + self.id + "_" + msg)
    
    def send(self, key:str, val:str):
        self._client.send('{"coil_' + self.id + '_' + key + '": ' + val + '}')        
    
    def activate(self):
        self._client.send('{"current_instrument":"COIL_' + self.id +'"}')
    
    def trigger(self):
        """trigger a tms pulse for the currently selected coil
        
        returns
        -------
        tstamp:float
            the pylsl timestamp when the trigger command was sent via TCP-IP
        """
        return self._client.trigger(self.id) 
    
    @property
    def id(self):
        """The coils id {0,1}
        
        localite can control 2 coils, this parameter identifies which one is
        controlled by this instance. Indexing starts at 0.
        """
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
        return True if self.request("position_control")['position_reached'] == "TRUE" else False
    
    @property
    def status(self):
        return self.request("status")
    
    @property
    def response(self):
        return self.request("response")
    
    def set_response(self, response, channel_idx:int=0):
        """send the response in localite

        THe TMS-Navigator software must be set to receive them. Do so by 
        selecting in 'Benutzereinstellungen', under "Stimulation Response",
        the option "JSONStimulationResponseSource.xml"

        Additionally, note that apparently, responses are queued, and processed 
        in FIFO at each triggered pulse, which means you could send a response
        before you actually triggered. Additionally, there is a time-out from
        the Localite-side, which is by default 10000ms, i.e. 10s. If the 
        response is send later than this time after the trigger, it is ignored
        for the correct trigger, and might instead be used inadvertently for
        a later trigger.

        args
        ----
        response:localite.response.Response
            the response class 
        channel_idx:int
            the channel for which to calculate the response
        """
        msg = response.as_json(channel_idx)
        self._client.send('{"coil_' + self.id + '_response": ' + msg + '}')