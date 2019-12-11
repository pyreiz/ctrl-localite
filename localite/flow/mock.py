import socket
import json
import pylsl
import threading
import time
from typing import List, Dict, Union
from pylsl import local_clock
from localite.flow.payload import Queue, get_from_queue, put_in_queue, Payload
from localite.flow.loc import localiteClient, ignored_localite_messages
from itertools import repeat


def append(outqueue: Queue, is_running: threading.Event, imi: float = 1):
    from queue import Full

    def Messages():
        continual = ignored_localite_messages + [{"coil_0_position": "None"}]
        while True:
            yield from continual

    message = Messages()
    while not is_running.is_set():
        time.sleep(0.1)
    print("Starting MOCK-MSG-QUEUE")
    while is_running.is_set():
        time.sleep(imi)
        msg = next(message)
        try:
            outqueue.put_nowait(msg)
        except Full:
            outqueue.get()
            outqueue.task_done()
            outqueue.put(msg)
        print("MOCK:APP", outqueue.unfinished_tasks)


def kill(host: str = "127.0.0.1", port=6666):
    client = localiteClient(host, port)
    msg = {"cmd": "poison-pill"}
    msg = json.dumps(msg)
    client.send(msg)


def responses(msg: Dict[str, Union[str, int]]) -> Dict:
    key = list(msg.keys())[0]
    val = msg[key]
    if key == "current_instrument":  # set current instrument
        return {val: "COIL_0"}
    if key in [
        "pointer_target_index",
        "coil_0_target_index",
        "coil_1_target_index",
    ]:  # set target index
        return {val: 1}
    elif key == "single_pulse":  # trigger
        if val in ["COIL_0", "COIL_1"]:
            return {val.lower() + "_didt": 11}
        else:
            return {"error", msg}
    elif key in ["coil_0_amplitude", "coil_1_amplitude"]:  # set amplitude
        if val > 0 and val < 100:
            return msg
        else:
            return {"error", msg}
    elif key in ["coil_0_response", "coil_1_response"]:  # set response
        if val["mepmaxtime"] < 0 or val["mepmaxtime"] > 100000:
            return {"error", msg}
        for subkey in ["mepamplitude", "mepmin", "mepmax"]:
            if val[subkey] < -51200 or val[subkey] > 51200:
                return False
            return True
    elif key == "get":
        valid = {"coil_0_amplitude":1,
                "coil_0_didt":99,
                "coil_0_position":{"q0":17., "qx":17., "qy": 17., "qz":17., "x":37, "y":77, "z": 53},
                "coil_0_position_control":{"position_reached":"TRUE", "index":1},
                "coil_0_response":{"mepmaxtime":18, "mepamplitude":50, "mepmin":-25, "mepmax": 25},,
                "coil_0_status":"OK",
                "coil_0_stimulator_connected":"TRUE",
                "coil_0_stimulator_mode":{"value":0, "name":"mock"},
                "coil_0_stimulator_model":{"value":0, "name":"mock"},
                "coil_0_stimulator_status":1,
                "coil_0_target_index":1,
                "coil_0_temperature":35,
                "coil_0_type":"Mock0704",
                "coil_0_waveform":{"value":1, "name": "mockphasic"},
                "coil_1_amplitude":1, 
                "coil_1_didt": 99,
                "coil_1_position": {"q0":17., "qx":17., "qy": 17., "qz":17., "x":37, "y":77, "z": 53},
                "coil_1_position_control": {"position_reached":"TRUE", "index":1},
                "coil_1_response":{"mepmaxtime":18, "mepamplitude":50, "mepmin":-25, "mepmax": 25},
                "coil_1_status":"OK"",
                "coil_1_stimulator_connected":"TRUE",
                "coil_1_stimulator_mode":{"value":0, "name":"mock"},
                "coil_1_stimulator_model":{"value":0, "name":"mock"},
                "coil_1_stimulator_status":1,
                "coil_1_target_index":1,
                "coil_1_temperature":35,
                "coil_1_type":"Mock0704",
                "coil_1_waveform":{"value":1, "name": "mockphasic"},
                "current_instrument":"COIL_0",
                "navigation_mode":"NAVIGATION",
                "patient_registration_status":"REGISTERED",
                "pointer_position":{"q0":17., "qx":17., "qy": 17., "qz":17., "x":37, "y":77, "z": 53},
                "pointer_position_control":{"position_reached":"TRUE", "index":1},
                "pointer_status":"OK",
                "pointer_target_index":1,
                "reference_status":"OK"
                }
        try:
            return {val: valid[val]}
        except KeyError:
            return {"error": msg}
    else:
        return {"error": msg}


class Mock(threading.Thread):
    def __init__(self, host: str = "127.0.0.1", port: int = 6666):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.is_running = threading.Event()

    def await_running(self):
        while not self.is_running.is_set():  # pragma no cover
            pass

    @staticmethod
    def read_msg(client: socket.socket) -> dict:
        "parse the message"
        t0 = time.time()
        client.settimeout(0.1)
        msg = b" "
        while True:
            try:
                prt = client.recv(1)
                msg += prt
                msg = json.loads(msg.decode("ascii"))
                return msg
            except json.JSONDecodeError as e:  # pragma no cover
                pass
            except socket.timeout:
                return None
            except Exception as e:  # pragma no cover
                print("MOCK:READ_MSG:", e)
                return None

    def run(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, self.port))
        listener.settimeout(1)
        listener.listen(1)  # one  unaccepted client is allowed
        outqueue = Queue(maxsize=10)
        outqueue.put({"coil_0_position": "None"})
        appender = threading.Thread(target=append, args=(outqueue, self.is_running,))
        appender.start()
        self.is_running.set()
        print("Starting MOCK")
        while self.is_running.is_set():
            try:
                client = None
                client, address = listener.accept()
                print("MOCK:CLIENT", address)
                msg = self.read_msg(client)
                if msg is not None:
                    print("MOCK:RECV", msg)
                    if "cmd" in msg.keys() and "poison-pill" in msg.values():
                        self.is_running.clear()
                        break
                    if "get" in msg.keys():
                        key = msg["get"]
                        # this client is not the localiteClient! but a simple socket
                        outqueue.put({key: "answer"})
                    if "single_pulse" in msg.keys():
                        outqueue.put({msg["single_pulse"].lower() + "_didt": 10})

                # always send a message, if there is none queued, wait
                # until one is available
                while outqueue.unfinished_tasks == 0:
                    time.sleep(0.01)
                if client is not None:
                    item = outqueue.get_nowait()
                    outqueue.task_done()
                    print("MRK:REM", item, outqueue.unfinished_tasks)
                    msg = json.dumps(item).encode("ascii")
                    client.sendall(msg)
                    client.close()
            except socket.timeout:
                client = None
            except (
                ConnectionError,
                ConnectionAbortedError,
                ConnectionResetError,
                ConnectionRefusedError,
            ):  # pragma no cover
                client = None
            except Exception as e:  # pragma no cover
                print("MOCK:RUN", str(e))

            time.sleep(0.001)
        print("Shutting MOCK down")

    def kill(self):
        kill(self.host, self.port)
