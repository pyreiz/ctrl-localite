# -*- coding: utf-8 -*-
"""
A client to communicate with the Localite to control the magventure.

@author: Robert Guggenberger
"""
import socket
import json
import pylsl
import threading
# %%
    
class MarkerStreamer(threading.Thread):    
    "LSL based software marker streamer"

    def __init__(self, name:str="localite_marker", host="127.0.0.1", port=6666): 
        threading.Thread.__init__(self)           
        self.host = host
        self.port = port        
        self.name = name
        self.is_running = threading.Event()
        
    def stop(self):
        self.queue.join()
        self.is_running.clear()
                
    def run(self):   
        source_id = socket.gethostname()
        info = pylsl.StreamInfo(self.name, type='Markers', channel_count=1, nominal_srate=0, 
                                channel_format='string', source_id=source_id)        
        outlet = pylsl.StreamOutlet(info)
        client = Client(host=self.host, port=self.port)
        client.timeout = None # no timeout
                
        self.is_running.set()
        print(info.as_xml())        
        while self.is_running.is_set(): 
            key, val = client.listen()
            if key in ('coil_0_didt', 'coil_1_didt'): #localite has triggered
                marker = json.dumps({key:val})
                tstamp = pylsl.local_clock()
                outlet.push_sample([marker])   
                print(f'Pushed {marker} at {tstamp}')
                
# %%            
class Client(object):
    """
     A LocaliteJSON socket client used to communicate with a LocaliteJSON socket server.

    example
    -------
    host = '127.0.0.1'
    port = 6666
    client = Client(True)
    client.connect(host, port).send(data)
    response = client.recv()        
    client.close()

    example
    -------
    response = Client().connect(host, port).send(data).recv_close()
    """

    socket = None

    def __init__(self, host, port=6666, timeout=3):        
        self.host = host
        self.port = port
        self.timeout= timeout
                
    def connect(self):
        'connect wth the remote server'
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket.settimeout(self.timeout)

    def close(self):
        'closes the connection'
        self.socket.shutdown(1)
        self.socket.close()
        del self.socket
        
    def write(self, data):
        self.socket.sendall(data.encode('ascii'))
        return self

    def read(self):
        'parse the message until it is a valid json'
        msg = bytearray(b' ')
        while True:
            try:
                prt = self.socket.recv(1)                    
                msg += prt                  
                key, val = self.decode(msg.decode('ascii')) # because the first byte is b' '                         
                return key, val
            except json.decoder.JSONDecodeError:
                pass
            except Exception as e:
                raise e       
    
    def listen(self):
        self.connect()
        msg = self.read()
        self.close()
        return msg
    
    def decode(self, msg:str, index=0):
        msg = json.loads(msg)
        key = list(msg.keys())[index]
        val = msg[key]
        return key, val
    
    def send(self, msg:str):
        self.connect()
        self.write(msg)
        self.close()
        
    def request(self, msg="coil_0_amplitude"):
        self.connect()
        msg = '{"get":\"' + msg + '\"}'
        self.write(msg)        
        key = val = ''    
        _, expected = self.decode(msg)   
        while key != expected:
            key, val = self.read()         
        self.close()        
        return None if val == 'NONE' else val

# c = Client(host=host)
# %timeit -n 1 -r 1000 c.request()        
# 5.22 ms ± 3.29 ms per loop (mean ± std. dev. of 1000 runs, 1 loop each)
