"""
User-interface to control the TMS
"""
from localite.flow.ext import push
from functools import partial
from localite.flow.mrk import Receiver


class Coil:
    """Coil is a user-friendly interface to control the TMS and Localite
    """

    def __init__(self, coil: int = 0, host: str = "127.0.0.1", port: int = 6667):
        self.id = coil
        self.receiver = Receiver(name="localite_marker")
        self.receiver.start()
        self.push_mrk = partial(push, fmt="mrk", host=host, port=port)
        self.push_loc = partial(push, fmt="loc", host=host, port=port)

    def push(self, msg: str):
        self.push_mrk(msg=msg)
        self.push_loc(msg=msg)

    def push_marker(self, marker: str):
        "pushes a str to the Marker-Stream running in the background"
        self.push_mrk(msg=marker)

    def send_key_val(self, key: str, val: str):
        self.push('{"coil_' + self.id + "_" + key + '": ' + val + "}")

    def activate(self):
        self.push('{"current_instrument":"COIL_' + self.id + '"}')

    def trigger(self):
        "trigger a single pulse"
        self.push('{"single_pulse": "coil_' + self.id + '"}')

    def request(self, msg: str) -> str:
        """receive an answer from localite 
        
        receive markers from the MRK outlet until the request has passed
        through the flow. The next available marker should be the answer
        """
        self.receiver.clear()
        self.push(msg)
        passed = False
        while not passed:
            try:
                if not passed:
                    passed = next(iter(self.receiver))[0] == msg
                else:
                    return next(iter(self.receiver))[0]
            except StopIteration:
                pass

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
        return self.request("type")

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
        self.send("target_index", str(index))
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
