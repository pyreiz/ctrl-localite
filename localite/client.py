# -*- coding: utf-8 -*-
"""
A client to communicate with the Localite to control the magventure.

@author: Robert Guggenberger
"""
import socket
import json
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

    def __del__(self):
        self.close()

    def __init__(self, host, port=6666):        
        self.host = host
        self.port = port
                
    def connect(self):
        'connect wth the remote server'
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket.settimeout(3)

    def close(self):
        'closes the connection'
        self.socket.shutdown(1)
        self.socket.close()

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
    
    def decode(self, msg:str, index=0):
        msg = json.loads(msg)
        key = list(msg.keys())[index]
        val = msg[key]
        return key, val
    
    def send(self, msg:str):
        self.connect()
        self.write(msg)
        self.close()
        
    def request(self, msg='{"get":"coil_0_amplitude"}'):
        self.connect()
        self.write(msg)        
        key = val = ''    
        _, expected = self.decode(msg)        
        while key != expected:
            key, val = self.read()            
        self.close()
        return key, val

# c = Client(host=host))
# %timeit -n 1 -r 1000 c.request()        
# 5.38 ms ± 244 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
# %%
# %timeit -n 1 -r 1000 c.send('{"coil_0_amplitude":45}')        
# 451 µs ± 12.6 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)
