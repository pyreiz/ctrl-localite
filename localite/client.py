# -*- coding: utf-8 -*-
"""
A client to communicate with the Localite to control the magventure.

@author: Robert Guggenberger
"""
import socket
import json
import pylsl
import threading
import time
# %%
def decode(msg):
  _brack_val = {'{': 1, '}': -1}
  _quota_val = {'"': 1, "'": 1}
  _colon_val = {'{': -1, ':': 2, '}': -1}
    
# %%
class SmartClient(threading.Thread):    
    "LSL based software marker streamer"

    instance = [None]
    @classmethod
    def get_running_instance(cls, **kwargs):
        if cls.instance[0] is None or not cls.instance[0].is_alive:
            cls.instance[0] = cls(**kwargs)
        if not cls.instance[0].is_running.is_set():
            cls.instance[0].start()            
        return cls.instance[0]            

    def __init__(self, name:str="localite_marker", host="127.0.0.1", port=6666): 
        threading.Thread.__init__(self)           
        self.host = host
        self.port = port        
        self.name = name    
        
        self.client_lock = threading.Lock()
        self.client = Client(host=self.host, port=self.port)
   
        source_id = socket.gethostname()
        self.info = pylsl.StreamInfo(self.name, type='Markers', channel_count=1, nominal_srate=0, 
                                channel_format='string', source_id=source_id)        
        self.outlet = pylsl.StreamOutlet(self.info)     
        self.outlet_lock = threading.Lock()

        self.is_running = threading.Event()        
        
    def stop(self):
        self.is_running.clear()
             
    def send(self, msg:str):
        with self.client_lock:
            try:
                self.client.send(msg)
                print(f'Send {msg} at {pylsl.local_clock()}')
            except ConnectionResetError or ConnectionRefusedError:
                print("Connection Problems. I'll keep on trying to connect")
                time.sleep(5)
                self.client = Client(host=self.host, port=self.port)
             
                    
    def request(self, msg):
        try:
            with self.client_lock:
                answer = self.client.request(msg)                        
        except ConnectionResetError or ConnectionRefusedError:
            print("Connection Problems. Retrying")
    
        print(f'Received {answer} for {msg} at {pylsl.local_clock()}')                
        return answer 
    
    def trigger(self, id:str):        
        marker = '{"single_pulse":"COIL_' + id + '"}'                
        try:                                
            with self.client_lock:
               self.client.send(marker)                                
        except ConnectionResetError or ConnectionRefusedError:
            print("Connection Problems. Aborting for safety")
            return False
                
        tstamp = pylsl.local_clock()
        print(f'Pushed {marker} at {tstamp}')
        with self.outlet_lock:            
            self.outlet.push_sample([marker], tstamp)                   
        
        return True
    
    def run(self):   
        self.is_running.set()
        print(self.info.as_xml())        
        while self.is_running.is_set():                
            try:
                with self.client_lock:    
                    key, val = self.client.listen()       
            except ConnectionResetError or ConnectionRefusedError:
                print("Connection Problems. Retrying")
            
            tstamp = pylsl.local_clock()            
            marker = json.dumps({key:val})                   
            if key in ('coil_0_didt', 'coil_1_didt'): #localite has triggered                
                print(f'Pushed {marker} at {tstamp}')
                with self.outlet_lock:
                    self.outlet.push_sample([marker], tstamp)                   
   
    
                
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

    def __init__(self, host, port=6666, timeout=None):        
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


    def read_byte(self, counter, buffer):
        """read next byte from the TCP/IP bytestream and decode as ASCII"""
        if counter is None:
             counter = 0
        char = self.socket.recv(1).decode('ASCII')
        buffer.append(char)
        counter += {'{': 1, '}': -1}.get(char, 0)
        return counter, buffer


    def read(self):
        'parse the message until it is a valid json'
        counter = None
        buffer = []
        while counter is not 0:
            counter, buffer = self.read_byte(counter, buffer)
        response = ''.join(buffer)
        return self.decode(response)

    def listen(self):
        self.connect()
        msg = self.read()
        self.close()
        return msg
    
    def decode(self, msg:str, index=0):
        msg = msg.replace('reason','\"reason\"') #catches and interface error    
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
        print(msg)
        print(expected)
        while key != expected:
            key, val = self.read()         
        self.close()        
        return None if val == 'NONE' else val

# c = Client(host=host)
# %timeit -n 1 -r 1000 c.request()        
# 5.22 ms ± 3.29 ms per loop (mean ± std. dev. of 1000 runs, 1 loop each)
