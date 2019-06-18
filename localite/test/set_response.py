# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 18:51:56 2019

@author: AGNPT-M-001
"""
import localite
coil = localite.Coil(host="134.2.117.173")
coil.trigger()
response = localite.Response._mock()
coil.set_response(response, channel_idx=0)
