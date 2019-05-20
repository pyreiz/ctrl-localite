# -*- coding: utf-8 -*-
"""
Created on Mon May 20 10:41:04 2019

@author: AGNPT-M-001
"""
from dataclasses import dataclass
import numpy as np
# %%
@dataclass
class Response():    
    chunk:np.ndarray
    tstamps:np.ndarray
    fs:int = 1000
    pre_in_ms:float = 25
    post_in_ms:float = 75
    onset_in_ms:float=None
        
    @property
    def onset(self):
        #onset = (self.tstamps>self.onset_in_ms)[:,0].argmax()
        onset = abs((self.onset_in_ms-self.tstamps)[:,0]).argmin()
        return onset 

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
        response = self.chunk[self.pre:self.post, channel_idx].copy()     
        response -= bl.mean()
        return response
    
    def get_vpp(self, channel_idx:int=0):        
        data = self.chunk[self.onset:self.post, channel_idx]                
        return data.max()-data.min()
    
    def remove_jitter(self, break_threshold_seconds=1,
                      break_threshold_samples=500):
        nsamples = len(self.tstamps)
        tdiff = 1.0 / self.fs if self.fs > 0 else 0.0
        self.rawtstamps = self.tstamps.copy()        
        if nsamples > 0 and self.fs > 0:
            # Identify breaks in the data
            diffs = np.diff(self.tstamps,axis=0)
            breaks_at = diffs > np.max((break_threshold_seconds,
                                        break_threshold_samples * tdiff))
            if np.any(breaks_at):
                indices = np.where(breaks_at)[0]
                indices = np.hstack((0, indices, indices, nsamples - 1))
                ranges = np.reshape(indices, (2, -1)).T
            else:
                ranges = [(0, nsamples - 1)]
    
            # Process each segment separately
            samp_counts = []
            durations = []
            self.effective_srate = 0
            for range_i in ranges:
                if range_i[1] > range_i[0]:
                    # Calculate time stamps assuming constant intervals within the segment.
                    indices = np.arange(range_i[0], range_i[1] + 1, 1)[:, None]
                    X = np.concatenate((np.ones_like(indices), indices), axis=1)
                    y = self.tstamps[indices,0]
                    mapping = np.linalg.lstsq(X, y, rcond=-1)[0]
                    self.tstamps[indices,0] = (mapping[0] + mapping[1] *
                                                   indices)
                    # Store num_samples and segment duration
                    samp_counts.append(indices.size)
                    durations.append((self.tstamps[range_i[1]] -
                                      self.tstamps[range_i[0]]) + tdiff)
            samp_counts = np.asarray(samp_counts)
            durations = np.asarray(durations)
            if np.any(samp_counts):
                self.effective_srate = np.sum(samp_counts) / np.sum(durations)
        else:
            self.effective_srate = 0
     
    def get_xaxis(self, stepsize=5):
        xticks = np.arange(0, self.post-self.pre, stepsize*1000/self.fs)
        xlim = (0, self.post-self.pre)
        xticklabels = (['{0:.0f}'.format(x) for x in np.arange(-self.pre_in_ms*1000/self.fs, (self.post_in_ms+stepsize)*1000/self.fs, stepsize)])
        return xticks, xticklabels, xlim