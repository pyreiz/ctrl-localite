import socket
import json
import pylsl
import threading
import time
from pylsl import local_clock
from localite.flow.payload import Queue, get_from_queue, put_in_queue, Payload

# %%
class localiteClient:
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


class LOC(threading.Thread):
    def __init__(self, outbox: Queue, inbox: Queue, host: str, port: int = 6666):
        threading.Thread.__init__(self)
        self.inbox = inbox
        self.outbox = outbox
        self.host = host
        self.port = port
        self.is_running = threading.Event()

    def await_running(self):
        while not self.is_running.is_set():
            pass

    def run(self):
        self.is_running.set()
        client = localiteClient(host=self.host, port=self.port)
        while self.is_running.is_set():
            payload = get_from_queue(self.inbox)
            if payload is None:
                continue
            if payload.fmt == "cmd":
                if payload.msg == "poison-pill":
                    self.is_running.clear()
                    break
            elif payload.fmt == "loc":
                answer = None
                if "get" in payload.msg:
                    answer = client.request(payload.msg)
                else:
                    client.send(payload.msg)
                if answer is not None:
                    pl = Payload("mrk", answer, local_clock())
                    put_in_queue(pl, self.outbox)

        print("Shutting LOC down")


# ------------------------------------------------------------------------------


class Mock(threading.Thread):
    def __init__(self, host: str = "127.0.0.1", port: int = 6666):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.is_running = threading.Event()

    def await_running(self):
        while not self.is_running.is_set():
            pass

    @staticmethod
    def read_msg(client: socket.socket) -> dict:
        "parse the message"
        msg = bytearray(b" ")
        while True:
            try:
                prt = client.recv(1)
                msg += prt
                msg = json.loads(msg.decode("ascii"))
                return msg
            except json.JSONDecodeError as e:  # pragma no cover
                pass
            except Exception as e:
                print(e)
                return None

    def run(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, self.port))
        listener.listen(1)  # one  unaccepted client is allowed
        self.is_running.set()
        while self.is_running.is_set():
            try:
                client, address = listener.accept()
                msg = self.read_msg(client)
                if msg is None:
                    continue
                if "cmd" in msg.keys() and "poison-pill" in msg.values():
                    self.is_running.clear()
                    break
                else:
                    client.send(json.dumps(msg))
            except Exception as e:
                print(e)
            finally:
                client.shutdown(socket.SHUT_WR)
                client.close()
        print("Shutting LOC-MOCK down")

    def kill(self):
        client = localiteClient(self.host, self.port)
        msg = {"cmd": "poison-pill"}
        msg = json.dumps(msg)
        client.send(msg)
