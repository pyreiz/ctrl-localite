"""
User-interface to control the TMS
"""
from localite.flow.ext import push
from functools import partial
from localite.flow.mrk import Receiver
from typing import Tuple


class Coil:
    """Coil is a user-friendly interface to control the TMS and Localite

    args

    coil: int = 0
        the coil to control, either 0 or 1
    address: Tuple[str, int] = ("127.0.0.1", 6667)
        the host, port of the EXT server of the localite-flow
    
    """

    def __init__(self, coil: int = 0, address: Tuple[str, int] = ("127.0.0.1", 6667)):
        self.id = coil
        self.receiver = Receiver(name="localite_marker")
        self.receiver.start()
        host, port = address
        self._push_mrk = partial(push, fmt="mrk", host=host, port=port)
        self._push_loc = partial(push, fmt="loc", host=host, port=port)

    def push(self, msg: str):
        self._push_loc(msg=msg)

    def push_marker(self, marker: str):
        "pushes a str to the Marker-Stream running in the background"
        self._push_mrk(msg=marker)

    def activate(self):
        self.push('{"current_instrument":"COIL_' + self.id + '"}')

    def trigger(self):
        "trigger a single pulse"
        self.push('{"single_pulse": "COIL_' + self.id + '"}')

    def request(self, msg: str) -> str:
        "request a property from localite"
        self._push_loc(msg=msg)
        return self.receiver.await_response(msg)

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
        self._id = coil

    @property
    def type(self):
        return self.request('{"get":"type"}')

    @property
    def temperature(self):
        return self.request("temperature")

    @property
    def waveform(self):
        return self.request("waveform")

    @property
    def stimulator_mode(self):
        return self.request("stimulator_mode")

    @property
    def didt(self):
        return self.request("didt")

    @property
    def amplitude(self):
        return self.request("amplitude")

    @amplitude.setter
    def amplitude(self, amplitude: int):
        self.send("amplitude", str(amplitude))
        return self.request("amplitude")

    @property
    def target_index(self):
        return self.request("target_index")

    @target_index.setter
    def target_index(self, index: int):
        self.request("target_index", str(index))
        return self.request("target_index")

    @property
    def position(self):
        return self.request("position")

    @property
    def position_reached(self):
        return (
            True
            if self.request("position_control")["position_reached"] == "TRUE"
            else False
        )

    @property
    def status(self):
        return self.request("status")


if __name__ == "__main__":

    self = Coil()

