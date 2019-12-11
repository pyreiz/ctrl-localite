import socket
import json
import pylsl
import threading
import time
from typing import List, Union, Dict
from pylsl import local_clock
from localite.flow.payload import Queue, get_from_queue, put_in_queue, Payload
from itertools import count

ignored_localite_messages = [
    {"pointer_status": "BLOCKED"},
    {"reference_status": "BLOCKED"},
    {"coil_1_status": "BLOCKED"},
    {"coil_0_status": "BLOCKED"},
]


def is_valid(payload: Payload) -> bool:
    try:
        if payload.fmt != "loc":
            return False
        msg = json.loads(payload.msg)
        key = list(msg.keys())[0]
        val = msg[key]

        if key == "current_instrument":
            if val in ["NONE", "POINTER", "COIL_0", "COIL_1"]:
                return True
        elif key in [
            "pointer_target_index",
            "coil_0_target_index",
            "coil_1_target_index",
        ]:
            if type(val) is int and val > 0:
                return True
        elif key == "single_pulse" and val in ["COIL_0", "COIL_1"]:
            return True
        elif key in ["coil_0_amplitude", "coil_1_amplitude"]:
            if val > 0 and val < 100:
                return True
        elif key in ["coil_0_response", "coil_1_response"]:
            if val["mepmaxtime"] < 0 or val["mepmaxtime"] > 100000:
                return False
            for subkey in ["mepamplitude", "mepmin", "mepmax"]:
                if val[subkey] < -51200 or val[subkey] > 51200:
                    return False
            return True
        elif key == "get":
            valid = {
                "coil_0_amplitude",
                "coil_0_didt",
                "coil_0_position",
                "coil_0_position_control",
                "coil_0_response",
                "coil_0_status",
                "coil_0_stimulator_connected",
                "coil_0_stimulator_mode",
                "coil_0_stimulator_model",
                "coil_0_stimulator_status",
                "coil_0_target_index",
                "coil_0_temperature",
                "coil_0_type",
                "coil_0_waveform",
                "coil_1_amplitude",
                "coil_1_didt",
                "coil_1_position",
                "coil_1_position_control",
                "coil_1_response",
                "coil_1_status",
                "coil_1_stimulator_connected",
                "coil_1_stimulator_mode",
                "coil_1_stimulator_model",
                "coil_1_stimulator_status",
                "coil_1_target_index",
                "coil_1_temperature",
                "coil_1_type",
                "coil_1_waveform",
                "current_instrument",
                "navigation_mode",
                "patient_registration_status",
                "pointer_position",
                "pointer_position_control",
                "pointer_status",
                "pointer_target_index",
                "reference_status",
            }
            if val in valid:
                return True
        else:
            return False
    except Exception:
        return False
    return False


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

    def read(self) -> Union[None, str]:
        "parse the message"
        bmsg = bytearray(b" ")
        while True:
            try:
                prt = self.socket.recv(1)
                bmsg += prt
                msg = json.loads(bmsg.decode("ascii"))
                return msg
            except json.JSONDecodeError as e:  # pragma no cover
                pass
            except Exception as e:  # pragma no cover
                print("LCL:READ:", e)
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
            print("LCL:RECV", key, val)
        self.close()
        return json.dumps({key: val})


def forward(client: localiteClient, payload: Payload) -> Union[str, None]:
    """forward a localite payload to the localite PC

    returns
    -------
    answer: Union[str, None]
        if the payload was a request, the response from the localite PC
        otherwise, None
    """
    if not is_valid(payload):
        print("LOC:INVALID", payload)
        return
    dec = json.loads(payload.msg)
    if "get" in dec.keys():
        answer = client.request(payload.msg)
        print("LOC:REQU", payload.msg)
    else:
        client.send(payload.msg)
        answer = None
        print("LOC:SENT", payload.msg)
    return answer


def listen_and_queue(
    client: localiteClient, ignore: List[Dict[str, str]], queue: Queue
) -> None:
    """listen to the localice stream and forward to queue
    """
    msg = client.listen()
    if msg in ignore or None:
        return
    else:
        print("LOC:MSG", msg)
        pl = Payload("mrk", msg, local_clock())
        put_in_queue(pl, queue)


class LOC(threading.Thread):
    def __init__(
        self,
        outbox: Queue,
        inbox: Queue,
        host: str,
        port: int = 6666,
        ignore: List[Dict[str, str]] = ignored_localite_messages,
    ):
        threading.Thread.__init__(self)
        self.inbox = inbox
        self.outbox = outbox
        self.ignore = ignore
        self.host = host
        self.port = port
        self.is_running = threading.Event()

    def await_running(self):  # pragma no cover
        while not self.is_running.is_set():
            pass

    def run(self):
        client = localiteClient(host=self.host, port=self.port)
        self.is_running.set()
        print(f"LOC {self.host}:{self.port} started")
        while self.is_running.is_set():
            try:
                payload = get_from_queue(self.inbox)
                if payload is None:
                    listen_and_queue(client, ignore=self.ignore, queue=self.outbox)
                elif payload.fmt == "cmd":
                    if payload.msg == "poison-pill":
                        self.is_running.clear()
                        break
                elif payload.fmt == "loc":
                    answer = forward(client, payload)
                    if answer is not None:
                        print("LOC:RECV:", answer)
                        pl = Payload("mrk", answer, local_clock())
                        put_in_queue(pl, self.outbox)
            except Exception as e:  # pragma no cover
                if self.is_running.set():
                    print("LOC:EXC", e)
                    pl = Payload("mrk", "LOC:EXC " + str(e), local_clock())
                    put_in_queue(pl, self.outbox)
                    self.is_running.clear()

        print("Shutting LOC down")
