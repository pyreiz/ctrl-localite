#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock LocaliteJSON Server for testing and debugging

@author: Robert Guggenberger
"""
import socket
import sys
import datetime

class MockServer(object):
    """
    A LocaliteJSON socket server used to communicate with a LocaliteJSON socket client.
    for testing purposes - replies with the message send

    example
    -------
    host = 127.0.0.1
    port = 6666
    server = Server(host, port)
    server.loop()
    """

    backlog = 5
    client = None

    def __init__(self, host, port, verbose):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen(self.backlog)
        self.verbose = verbose
        print('Creating TestServer at', host, ':', port)

    def __del__(self):
        self.close()

    def accept(self):
        # if a client is already connected, disconnect it
        if self.client:
            self.client.close()
        self.client, self.client_addr = self.socket.accept()
        return self

    def send(self, data):
        if not self.client:
            raise Exception('Cannot send data, no client is connected')
        _send(self.client, data)
        return self

    def recv(self):
        if not self.client:
            raise Exception('Cannot receive data, no client is connected')
        return _recv(self.client)

    def loop(self):
        try:
            while True:
                self.accept()
                data = self.recv()
                if self.verbose:
                    print('Received', data, 'from', self.client_addr, 'at', datetime.datetime.now())
                self.send(data)
        except Exception as e:
            raise e
        finally:
            self.close()
            
    def close(self):
        if self.client:
            self.client.close()
            self.client = None
        if self.socket:
            self.socket.close()
            self.socket = None



# helper functions #
def _send(socket, data):
    try:        
        serialized = data.encode('ASCII')
    except (TypeError, ValueError):
        raise Exception('Message is not serializable')
    socket.sendall(serialized)


def _recv(socket):
    # read ASCII letter by letter until we reach a zero count of +{-}
    def parse(counter, buffer):  
        if counter is None:              
            counter = 0
        char = socket.recv(1).decode('ASCII')            
        buffer.append(char)
        if char is '{':
            counter += 1
        if char is '}':
            counter -= 1
        return counter, buffer  
   
    buffer = []
    counter = None
    while counter is not 0:
        counter, buffer = parse(counter, buffer)
        # print(counter, buffer[-1])
               
    buffer = ''.join(buffer)  
    return buffer    

def myip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def parse_message():
    try:
        data = sys.argv[sys.argv.index('-m')+1]
        if data[0] is '-':
            raise IndexError
    except IndexError:
        data = '{"missing":"message"}'
    return data

def single_command_only():
    print('Choose either -m for message or -t for TestServer')
    quit()

def show_help():
    print('''
    Specify arguments
    -----------------

    -m for message
    -t Start a test-server
    -p followed by port, defaults to 6666
    -h followed by host, defaults to ip adress
    -v turn verbose on

    Example
    -------
    python LocaliteJSON.py -h 127.0.0.1 -p 6666 -m '{"test":"message"}'

    Example
    -------
    python LocaliteJSON.py -h 127.0.0.1 -p 6666 -t

        ''')
    quit()

class Messages():
    gci = "{'get':'current_instrument'}"
# %%
if __name__ == '__main__': 
    if len(sys.argv) < 2 or '-help' in sys.argv:
        show_help()

    # set defaults
    host = myip()
    port = 6666
    verbose = False

    if '-h' in sys.argv:
        host = sys.argv[sys.argv.index('-h')+1]
    if '-p' in sys.argv:
        port = int(sys.argv[sys.argv.index('-p')+1])
    if  '-v' in sys.argv:
        verbose = True
    if '-t' in sys.argv and '-m' in sys.argv:
        single_command_only()
        quit()

    # start test server
    if '-t' in sys.argv:
        server = MockServer(host, port, verbose)            
        server.loop()
    # start client socket    
