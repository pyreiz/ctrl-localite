# -*- coding: utf-8 -*-
"""
A client to communicate with the Localite to control the magventure.

@author: Robert Guggenberger
"""
# %%
import socket
import json
import pylsl
import threading
import time
from typing import Callable
from logging import getLogger
logger = getLogger("LocaliteClient")

def is_port_in_use(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def get_client(host='127.0.0.1', port=6666):
    if is_port_in_use("127.0.0.1", port+1):
        kill_client()
    client = SmartClient(host=host, port=port)
    return client.start()

def kill_client(host='127.0.0.1', port=6667):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        msg = json.dumps({"command":"die"}).encode("ascii")
        s.send(msg)



# %%
class SmartClient():
    def __init__(self, name:str="localite_marker", host:str="127.0.0.1", port:int=6666):
        self.name = name
        self.port = port
        self.host = host

    def stop(self):
        kill_client()

    def start(self):
        port = self.port
        host = self.host
        name = self.name
        client = ReceiverClient(name=name, host=host, port=port)
        killer = ReceiverServer(host="127.0.0.1", port=port+1, foo=client.stop)
        client.start()
        killer.start()
        return client
    

# %%

def read_msg(client):
    'receive byte for byte to read the header telling the message length'
    #parse the message until it is a valid json 
    msg = bytearray(b' ')
    while True:
        try:
            prt = client.recv(1)                    
            msg += prt                  
            return json.loads(msg.decode('ascii')) # because the first byte is b' '                     
        except json.decoder.JSONDecodeError:
            pass
        except Exception as e:
            print(e)
            break
        
    return None

class ReceiverServer(threading.Thread):

    def __init__(self, host="127.0.0.1", port: int = 6667, foo:Callable=None):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.stop_client = foo
        self.is_running = threading.Event()

    def stop(self):
        self.is_running.clear()

    def run(self):
        interface = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        interface.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        interface.settimeout(1)
        interface.bind((self.host, self.port))
        interface.listen(1)
        print('Server managing Localite Clients opened at {0}:{1}'.format(
            self.host, self.port))
        self.is_running.set()
        while self.is_running.is_set():
            message = {"command":"live"}
            try:
                client, address = interface.accept()
                try:
                    message = read_msg(client)
                except socket.timeout:
                    print('Client from {address} timed out')
                finally:
                    client.shutdown(2)
                    client.close()
            except socket.timeout:
                pass

            if message["command"] == "die":
                print("Attempting to stop client")
                self.stop_client()
                self.stop()
        else:
            print("Shutting down ReceiverServer at", self.host, self.port)



# %%


class ReceiverClient(threading.Thread):
    "LSL based software marker streamer"

    def __init__(self, name:str="localite_marker", host:str="127.0.0.1",    port=6666):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.name = name

        self.client_lock = threading.Lock()
        self.client = Client(host=self.host, port=self.port)

        source_id = '_'.join((socket.gethostname(), name))
        self.info = pylsl.StreamInfo(self.name, type='Markers', channel_count=1,
                                     nominal_srate=0, channel_format='string', source_id=source_id)
        self.outlet = pylsl.StreamOutlet(self.info)
        self.outlet_lock = threading.Lock()
        self.is_running = threading.Event()

    def stop(self):
        print("Attempting to stop")
        self.is_running.clear()
        print("Shutting down ReceiverClient for", self.host, self.port)  
        del self.outlet

    def run(self):
        print('Client manager listing to localite opened at {0}:{1}'.format(
            self.host, self.port))
        self.is_running.set()
        print(self.info.as_xml())
        while self.is_running.is_set():
            try:
                with self.client_lock:
                    key, val = self.client.listen()
            except (ConnectionResetError, ConnectionRefusedError):
                print("Connection Problems. Check that host={self.host} is valid.")

            tstamp = pylsl.local_clock()
            marker = json.dumps({key: val})

            if key in ('coil_0_didt', 'coil_1_didt'):  # localite has triggered
                print(f'Pushed {marker} at {tstamp}')
                with self.outlet_lock:
                    self.outlet.push_sample([marker], tstamp)
        else:
            print("Shutting down ReceiverClient for", self.host, self.port)  
 
    def send(self, msg: str):
        with self.client_lock:
            try:
                self.client.send(msg)
                print(f'Send {msg} at {pylsl.local_clock()}')
            except (ConnectionResetError, ConnectionRefusedError):
                print("Connection Problems. I'll keep on trying to connect")
                time.sleep(5)
                self.client = Client(host=self.host, port=self.port)

    def request(self, msg):        
        try:
            with self.client_lock:
                answer = self.client.request(msg)
            print(f'Received {answer} for {msg} at {pylsl.local_clock()}')
            return answer
        except (ConnectionResetError, ConnectionRefusedError):
            print("Connection Problems. Retry")
            return None

    def trigger(self, id: str):
        marker = '{"single_pulse":"COIL_' + id + '"}'
        try:
            with self.client_lock:
                self.client.send(marker)
        except (ConnectionResetError, ConnectionRefusedError):
            print("Connection Problems. Aborting for safety")
            return None

        tstamp = pylsl.local_clock()
        print(f'Pushed {marker} at {tstamp}')
        with self.outlet_lock:
            self.outlet.push_sample([marker], tstamp)

        return tstamp

    def push_marker(self, marker:str):

        tstamp = pylsl.local_clock()

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
        self.timeout = timeout

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

    def decode(self, msg: str, index=0):
        # catches and interface error
        msg = msg.replace('reason', '\"reason\"')
        try:
            decoded = json.loads(msg)
        except json.JSONDecodeError as e:
            print("JSONDecodeError: " + msg)
            raise e

        key = list(decoded.keys())[index]
        val = decoded[key]
        return key, val

    def send(self, msg: str):
        self.connect()
        self.write(msg)
        self.close()

    def request(self, msg="coil_0_amplitude"):
        self.connect()
        msg = '{"get":\"' + msg + '\"}'
        self.write(msg)
        key = val = ''
        _, expected = self.decode(msg)
        logger.debug(msg)
        logger.debug(expected)
        while key != expected:
            key, val = self.read()
        self.close()
        return None if val == 'NONE' else val


# c = Client(host=host)
# %timeit -n 1 -r 1000 c.request()
# 5.22 ms ± 3.29 ms per loop (mean ± std. dev. of 1000 runs, 1 loop each)
if __name__ == "__main__":

    client = get_client(host="134.2.117.173")
  
