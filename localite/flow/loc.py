import socket
import json
import pylsl
import threading
import time

# %%
class LOC(threading.Thread):
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

    def __init__(self, host: str, port: int = 6666):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port

    def connect(self):
        "connect wth the remote server"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket.settimeout(None)

    def close(self):
        "closes the connection"
        self.socket.shutdown(socket.SHUT_WR)
        self.socket.close()
        del self.socket

    def write(self, data):
        self.socket.sendall(data.encode("ascii"))
        return self

    def read_byte(self, counter, buffer):
        """read next byte from the TCP/IP bytestream and decode as ASCII"""
        if counter is None:
            counter = 0
        char = self.socket.recv(1).decode("ASCII")
        buffer.append(char)
        counter += {"{": 1, "}": -1}.get(char, 0)
        return counter, buffer

    def read(self):
        "parse the message until it is a valid json"
        counter = None
        buffer = []
        while counter is not 0:
            counter, buffer = self.read_byte(counter, buffer)
        response = "".join(buffer)
        return self.decode(response)

    def listen(self):
        self.connect()
        msg = self.read()
        self.close()
        return msg

    def decode(self, msg: str, index=0):
        # msg = msg.replace("reason", '"reason"')  # catches and interface error
        try:
            decoded = json.loads(msg)
        except json.JSONDecodeError:
            print("JSONDecodeError for:", msg)

        key = list(decoded.keys())[index]
        val = decoded[key]
        return key, val

    def send(self, msg: str):
        self.connect()
        self.write(msg)
        self.close()

    def request(self, msg="coil_0_amplitude"):
        self.connect()
        msg = '{"get":"' + msg + '"}'
        self.write(msg)
        key = val = ""
        _, expected = self.decode(msg)
        while key != expected:
            key, val = self.read()
        self.close()
        return None if val == "NONE" else val

