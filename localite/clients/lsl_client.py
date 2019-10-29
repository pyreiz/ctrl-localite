# -*- coding: utf-8 -*-
"""
A client to communicate with the Localite to control the magventure.

@author: Robert Guggenberger
"""
# %%
import socket
import json
import pylsl
import time
import threading
import argparse
import sys
from logging import getLogger
logger = getLogger("LocaliteLSL")

# %%


def decode(msg: str, index=0):
    # catches  interface error
    msg = msg.replace('reason', '\"reason\"')
    try:
        decoded = json.loads(msg)
    except json.JSONDecodeError as e:
        print("JSONDecodeError: \"" + msg + "\"")
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
        self.lock = threading.Lock()
        self.qlock = threading.Lock()
        self.queue = []

    def connect(self):
        'connect wth the remote server'
        self.lock.acquire()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket.settimeout(self.timeout)

    def close(self):
        'closes the connection'
        self.socket.shutdown(1)
        self.socket.close()
        self.lock.release()
        del self.socket

    def listen(self):
        with self.qlock:
            while len(self.queue) > 0:
                msg = self.queue.pop()
                self.send(msg)

        self.connect()
        try:
            tstamp = pylsl.local_clock()
            key, val = read_msg(self.socket)
        finally:
            self.close()
        return key, val, tstamp

    def request_response(self, coil_id):
        def append():
            msg = '"{\"get\":\"coil_' + coil_id + '_response\"}'
            self.qlock.acquire()
            self.queue.append(msg)
            self.qlock.release()
        t = threading.Timer(1, append)
        t.start()

    def send(self, msg: str):
        self.connect()
        self.socket.sendall(msg.encode('ascii'))
        print(f'Send {msg} at {pylsl.local_clock()}')
        self.close()


class LocaliteLSL(threading.Thread):
    "LSL based software marker streamer"

    def __init__(self, name: str = "localiteLSL", host: str = "127.0.0.1",
                 port=6666):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.name = name
        self.is_running = threading.Event()

    def run(self):
        self.is_running.set()
        print(f"Looking at {self.host}:{self.port} for a localite server.")
        self.client = Client(host=self.host, port=self.port)
        source_id = '_'.join((socket.gethostname(), self.name, self.host))
        info = pylsl.StreamInfo(self.name, type='Markers', channel_count=1,
                                nominal_srate=0, channel_format='string',
                                source_id=source_id)

        found = pylsl.resolve_byprop("source_id", info.source_id(), timeout=3)
        if found:
            print(found[0].as_xml())
            print("There is already a localiteLSL with the same source_id running")
            sys.exit(1)

        outlet = pylsl.StreamOutlet(info)
        print(info.as_xml())
        while self.is_running.is_set():
            try:
                key, val, tstamp = self.client.listen()
            except (ConnectionResetError, ConnectionRefusedError):
                print("Connection Problems. Retrying")
                time.sleep(1)
                continue

#            print("Ignoring", json.dumps(
#                {key: val}), "at", pylsl.local_clock())
            if key in ('coil_0_didt', 'coil_1_didt'):  # localite has triggered
                marker = json.dumps({key: val})
                print(f'Pushed {marker} at {tstamp}')
                outlet.push_sample([marker], tstamp)
                # request the response
                coil_id = key.split('_')[1]
                self.client.request_response(coil_id)

            elif key in ("error"):
                print(json.dumps({key: val}))
            elif val == "null":
                pass
            elif key.split('_')[1] in ("0", "1"):
                marker = json.dumps({key: val})
                print(f'Pushed {marker} at {tstamp}')
                outlet.push_sample([marker], tstamp)

    def stop(self):
        self.is_running.clear()
        print("Shutting down LocaliteLSL listening at", self.host, self.port)


def main():
    parser = argparse.ArgumentParser(prog='localiteLSL')
    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="the host at which the localite server resides")
    parser.add_argument("--port", type=int, default=6666,
                        help="the port of the localite server")

    args, unknown = parser.parse_known_args()
    client = LocaliteLSL(host=args.host, port=args.port)
    client.start()


if __name__ == "__main__":
    main()
