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
logger = getLogger("LocaliteLSL")
# %%


def decode(msg: str, index=0):
    # catches  interface error
    msg = msg.replace('reason', '\"reason\"')
    try:
        decoded = json.loads(msg)
    except json.JSONDecodeError as e:
        print("JSONDecodeError: " + msg)
        raise e
    key = list(decoded.keys())[index]
    val = decoded[key]
    return key, val


def read_byte(socket, counter, buffer):
    "read next byte from the TCP/IP bytestream and decode as ASCII"
    if counter is None:
        counter = 0
    char = socket.recv(1).decode('ASCII')
    buffer.append(char)
    counter += {'{': 1, '}': -1}.get(char, 0)
    return counter, buffer


def read_msg(socket):
    'parse the message until it is a valid json'
    counter = None
    buffer = []
    while counter != 0:
        counter, buffer = read_byte(socket, counter, buffer)
    response = ''.join(buffer)
    key, val = decode(response)
    return key, val


class Client(object):

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

    def listen(self):
        self.connect()
        try:
            tstamp = pylsl.local_clock()
            key, val = read_msg(self.socket)
        finally:
            self.close()
        return key, val, tstamp


class LocaliteLSL(threading.Thread):
    "LSL based software marker streamer"

    def __init__(self, name: str = "localite_marker", host: str = "127.0.0.1",
                 port=6666):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.name = name
        self.is_running = threading.Event()

    def run(self):
        self.is_running.set()
        self.client = Client(host=self.host, port=self.port)
        source_id = '_'.join((socket.gethostname(), self.name))
        info = pylsl.StreamInfo(self.name, type='Markers', channel_count=1,
                                nominal_srate=0, channel_format='string',
                                source_id=source_id)
        outlet = pylsl.StreamOutlet(info)
        print(info.as_xml())
        while self.is_running.is_set():
            try:
                key, val, tstamp = self.client.listen()
            except (ConnectionResetError, ConnectionRefusedError):
                print("Connection Problems. Retrying")
                continue

            if key in ('coil_0_didt', 'coil_1_didt'):  # localite has triggered
                marker = json.dumps({key: val})
                print(f'Pushed {marker} at {tstamp}')
                outlet.push_sample([marker], tstamp)

    def stop(self):
        self.is_running.clear()
        print("Shutting down LocaliteLSL listening at", self.host, self.port)


if __name__ == "__main__":
    client = LocaliteLSL()
    client.start()
