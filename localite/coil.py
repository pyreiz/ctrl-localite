"""
User-interface to control the TMS
"""
from localite.flow.ext import push
from functools import partial
from localite.flow.mrk import Receiver
from typing import Tuple, Dict, Any, Union
import json
import time

def pythonize_values(v: str) -> Union[bool, None, str]:
    "pythonize a dictionaries values"
    if type(v) is not str:
        return v
    if v.upper() == "TRUE":
        return True
    elif v.upper() == "FALSE":
        return False
    elif v.upper() == "NONE":
        return None
    else:
        return v


def pythonize_response(response: Dict[str, Any]) -> Any:
    "convert the json responses to a python builtin"
    for k, v in response.items():
        pass
    if type(v) is str:
        v = pythonize_values(v)
    elif type(v) is dict:
        d = dict()
        for _k, _v in v.items():
            d[_k] = pythonize_values(_v)
        return d
    return v


class Coil:
    """Coil is a user-friendly interface to control the TMS and Localite

    args

    coil: int = 0
        the coil to control, either 0 or 1
    address: Tuple[str, int] = ("127.0.0.1", 6667)
        the host, port of the EXT server of the localite-flow
    
    """

    def __init__(self, coil: int = 0, address: Tuple[str, int] = ("127.0.0.1", 6667), timeout=10):
        host, port = address
        self._push_mrk = partial(push, fmt="mrk", host=host, port=port)
        self._push_loc = partial(push, fmt="loc", host=host, port=port)
        self.receiver = Receiver(name="localite_marker")
        self.receiver.start()
        start_receiver_time = time.time()
        while not self.receiver.is_running.is_set():
            if time.time() > start_receiver_time + timeout:
                raise ConnectionError("Could not connect to localite flow")
            pass
        self.id = coil

    def await_connection(self):
        print("[", end="")
        while not self.connected:  # pragma no cover
            print(".", end="")
        print("]")

    def stream_info(self):
        self.type
        self.model
        self.mode
        self.waveform
        self.amplitude

    def push(self, msg: str):
        self._push_loc(msg=msg)

    def push_marker(self, marker: str):
        "pushes a str to the Marker-Stream running in the background"
        self._push_mrk(msg=marker)

    def trigger(self):
        "trigger a single pulse"
        self.push('{"single_pulse": "COIL_' + self.id + '"}')
        return self.didt

    def request(self, msg: str) -> Any:
        "add the coil id to the message and request a property from localite"
        msg = json.dumps({"get": f"coil_{self.id}_{msg}"})
        return self._request(msg)

    def _request(self, msg: str) -> Any:
        "request a ready made property from localite"
        self._push_loc(msg=msg)
        response, ts = self.receiver.await_response(msg)
        return pythonize_response(response)

    @property
    def connected(self) -> bool:
        "whether a stimulator is connected or not"
        return self.request("stimulator_connected")

    @property
    def id(self):
        """The coils id {0,1}

        localite can control 2 coils, this parameter identifies which one is
        controlled by this instance. Indexing starts at 0.
        """
        return str(self._id)

    @id.setter
    def id(self, coil: int = 0):
        if coil not in (0, 1):
            raise ValueError("Coil must be 0  or 1")
        self.push('{"current_instrument":"COIL_' + str(coil) + '"}')
        self._id = coil

    @property
    def type(self):
        return self.request("type")

    @property
    def temperature(self) -> int:
        return self.request("temperature")

    @property
    def didt(self) -> Union[int, None]:
        "the di/dt of the last succesfull TMS pulse"
        response = self.request("didt")
        # if there was not yet a stimulus, localite returns an error message
        # we skip that and just return 0
        if type(response) is dict and "reason" in response.items():  # pragma no cover
            return None
        else:
            return response

    @property
    def amplitude(self) -> int:
        "set the amplitude to MSO%"
        return self.request("amplitude")

    @amplitude.setter
    def amplitude(self, amplitude: int) -> int:
        "get the current amplitude in MSO%"
        msg = f'{{"coil_{self._id}_amplitude": {amplitude}}}'
        self._push_loc(msg=msg)
        return self.request("amplitude")

    @property
    def target_index(self) -> int:
        "get the current targets index"
        return self.request("target_index")

    @target_index.setter
    def target_index(self, index: int) -> int:
        "set the index of the next target"
        if index < 0:
            raise ValueError("Index must be higher than 0")
        msg = json.dumps({f"coil_{self._id}_target_index": index})
        self._push_loc(msg=msg)        
        return self.request("target_index")

    @property
    def position(self) -> Union[dict, None]:
        """the current position of the coil
        
        e.g. {"q0": 17.0,"qx": 17.0, "qy": 17.0, "qz": 17.0, 
              "x": 37, "y": 77, "z": 53}
        """
        return self.request("position")

    @property
    def position_reached(self) -> bool:
        "whether the target position has been reached or not"
        return self.request("position_control")["position_reached"]

    @property
    def visible(self) -> bool:
        "whether the coil can be seen by the NDI camera or not"
        return True if self.request("status") == "OK" else False

    @property
    def waveform(self) -> str:
        """the waveform currently set in the stimulator
        
        can be e.g. 'Monophasic', 'Biphasic', 'Halfsine', 'Biphasic Burst'
        """
        return self.request("waveform")["name"]

    @property
    def model(self) -> str:
        """the name of the stimulator model
        
        e.g. 'MagVenture 65 X100 + Option'
        """
        typ = self.request("type")
        model = self.request("stimulator_model")["name"]
        return " ".join((typ, model))

    @property
    def mode(self) -> str:
        """the mode of the stimulator
        
        can be e.g. 'Power', 'Twin', 'Dual', 'Standard'
            
        """
        return self.request("stimulator_mode")["name"]

    def set_response(
        self, mepmaxtime: float, mepamplitude: float, mepmin: float, mepmax: float
    ):
        key = f"coil_{self.id}_response"
        msg = {
            key: {
                "mepmaxtime": mepmaxtime,
                "mepamplitude": mepamplitude,
                "mepmin": mepmin,
                "mepmax": mepmax,
            }
        }
        self._push_loc(msg=json.dumps(msg))

