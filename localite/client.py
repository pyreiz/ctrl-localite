import socket
from pylsl import local_clock
import json
from typing import Dict, Any


class Client:
    "Basic Client communicating with the MarkerServer"

    def __init__(self, host="127.0.0.1", port: int = 6667, verbose=True):
        self.host = host
        self.port = port
        self.verbose = verbose

    def push(self, marker: Dict[str, Any] = {"command": "ping"},
             tstamp: float = None):
        "connects, sends a message, and closes the connection"
        self.connect()
        self.write(marker, tstamp)
        self.close()

    def connect(self):
        "connect wth the remote server"
        self.interface = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.interface.connect((self.host, self.port))
        self.interface.settimeout(1)

    def write(self, marker, tstamp):
        "encode message into ascii and send all bytes"
        msg = json.dumps((marker, tstamp)).encode("ascii")
        if self.verbose:
            print(f"Sending {marker} at {tstamp}")
        self.interface.sendall(msg)

    def close(self):
        "closes the connection"
        self.interface.shutdown(1)
        self.interface.close()


def available(port: int = 6667, host: str = "127.0.0.1", verbose=True) -> bool:
    """test whether a markerserver is already available at port

    args
    ----

    host: str
        the ip of the markerserver (defaults to localhost)

    port: int
        the port number of the markerserver (defaults to 6667)

    returns
    -------

    status: bool
        True if available, False if not
    """
    c = Client(host=host, port=port)
    try:
        c.push({"command": "ping"}, local_clock())
        return True
    except ConnectionRefusedError as e:
        if verbose:
            print(e)
            print(f"Markerserver at {host}:{port} is not available")
        return False
