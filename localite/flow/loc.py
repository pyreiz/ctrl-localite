import socket
import json
import pylsl
import threading
import time
from typing import List
from pylsl import local_clock
from localite.flow.payload import Queue, get_from_queue, put_in_queue, Payload


ignored_localite_messages = [
    {"pointer_status": "BLOCKED"},
    {"reference_status": "BLOCKED"},
    {"coil_1_status": "BLOCKED"},
    {"coil_0_status": "BLOCKED"},
]

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

    def write(self, msg: str):
        self.socket.sendall(msg.encode("ascii"))
        return self

    def read(self) -> dict:
        "parse the message"
        msg = bytearray(b" ")
        while True:
            try:
                prt = self.socket.recv(1)
                msg += prt
                msg = json.loads(msg.decode("ascii"))
                return msg
            except json.JSONDecodeError as e:  # pragma no cover
                pass
            except Exception as e:  # pragma no cover
                print("locCLIENT:READ:", e)
                return None

    def listen(self):
        self.connect()
        msg = self.read()
        self.close()
        return msg

    def send(self, msg: str):
        self.connect()
        self.write(msg)
        self.close()

    def request(self, msg: str = '{"get":"coil_0_amplitude"}'):
        self.connect()
        self.write(msg)
        key = val = ""
        expected = json.loads(msg)["get"]
        while key != expected:
            answer = self.read()
            key = list(answer.keys())[0]
            val = answer[key]
            val = None if val == "NONE" else val
            print("locCLIENT:RECV", key, val)
        self.close()
        return json.dumps({key: val})


class LOC(threading.Thread):
    def __init__(self, outbox: Queue, inbox: Queue, host: str, port: int = 6666):
        threading.Thread.__init__(self)
        self.inbox = inbox
        self.outbox = outbox
        self.host = host
        self.port = port
        self.is_running = threading.Event()

    def await_running(self):  # pragma no cover
        while not self.is_running.is_set():
            pass

    def run(self):
        self.is_running.set()
        client = localiteClient(host=self.host, port=self.port)
        print("Starting LOC")
        while self.is_running.is_set():
            payload = get_from_queue(self.inbox)
            if payload is None:
                msg = client.listen()
                print("LOC:MSG", msg)
                if msg in ignored_localite_messages:
                    continue
                else:
                    pl = Payload("mrk", msg, local_clock())
                    put_in_queue(pl, self.outbox)

            elif payload.fmt == "cmd":
                if payload.msg == "poison-pill":
                    self.is_running.clear()
                    break
            elif payload.fmt == "loc":
                answer = None
                dec = json.loads(payload.msg)
                if "get" in dec.keys():
                    answer = client.request(payload.msg)
                    print("LOC:REQU", payload.msg)
                else:
                    client.send(payload.msg)
                    print("LOC:SENT", payload.msg)
                if answer is not None:
                    print("LOC:RECV:", answer)
                    pl = Payload("mrk", answer, local_clock())
                    put_in_queue(pl, self.outbox)

        print("Shutting LOC down")
