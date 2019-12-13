import socket
import threading
import json
from localite.flow.payload import Payload, has_poison, Queue, put_in_queue
from localite.flow.lsl import local_clock
from typing import Dict, Any
from subprocess import Popen
from typing import Union, Tuple


class InvalidPayload(Exception):
    pass


def encode_payload(payload: Payload) -> bytes:
    tupled = (payload.fmt, payload.msg, payload.tstamp)
    return json.dumps(tupled).encode("ascii")


def decode_payload(buffer: bytes) -> Union[Payload, None]:
    try:
        fmt, msg, tstamp = json.loads(buffer.decode("ascii"))
        payload = Payload(fmt, msg, tstamp)
        if payload.fmt in ("cmd", "mrk", "loc"):
            return payload
        else:
            raise InvalidPayload(f"({fmt}, {msg}, {tstamp}) is no valid Payload")
    except json.decoder.JSONDecodeError:
        return None


def read_msg(client: socket.socket) -> Payload:
    """parse the message until it is a valid Payload and return the first"""
    msg = bytearray(b" ")
    while True:
        try:
            prt = client.recv(1)
            msg += prt
            payload = decode_payload(msg)
            if payload is not None:
                return payload
        except Exception as e:  # pragma no cover
            print(e)
            return None


# -----------------------------------------------------------------------------
class EXT(threading.Thread):
    def __init__(self, queue: Queue, host: str = "127.0.0.1", port: int = 6667):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.queue = queue
        self.is_running = threading.Event()

    def await_running(self):
        while not self.is_running.is_set():
            pass

    def run(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, self.port))
        listener.listen(1)  # one  unaccepted client is allowed
        self.is_running.set()
        print(f"EXT {self.host}:{self.port} started")
        while self.is_running.is_set():
            try:
                client, address = listener.accept()
                payload = read_msg(client)
                print(f"EXT:RECV {payload}")
                if not payload:
                    continue
                put_in_queue(payload, self.queue)
                if has_poison(payload):
                    self.is_running.clear()
                    break
            except Exception as e:  # pragma no cover
                print(e)
            finally:
                client.shutdown(socket.SHUT_RDWR)
                client.close()
        print("Shutting EXT down")


# ------------------------------------------------------------------------------
class Client:
    "Basic Client communicating with the MarkerServer"

    def __init__(self, host="127.0.0.1", port: int = 6667, verbose=True):
        self.host = host
        self.port = port
        self.verbose = verbose

    def push(self, payload: Payload, tstamp: float = None):
        "connects, sends a message, and closes the connection"
        self.connect()
        self.write(payload)
        self.close()

    def connect(self):
        "connect wth the remote server"
        self.interface = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.interface.connect((self.host, self.port))
        self.interface.settimeout(1)

    def write(self, payload: Payload):
        "encode message into ascii and send all bytes"
        msg = encode_payload(payload)
        if self.verbose:
            print(f"PUSH: {payload}")
        self.interface.sendall(msg)

    def close(self):
        "closes the connection"
        self.interface.shutdown(1)
        self.interface.close()


def push_payload(
    payload: Payload, host="127.0.0.1", port: int = 6667, verbose=True,
):
    "a functional interface to pushing a message"
    try:
        Client(host=host, port=port, verbose=verbose).push(payload)
        return True
    except (ConnectionRefusedError, ConnectionResetError) as e:
        if verbose and payload.msg != "ping":  # pragma no cover
            print(e)
            print(f"Localite EXT at {host}:{port} is not available")
        return False


def push(
    fmt: str,
    msg: str,
    tstamp: int = None,
    host="127.0.0.1",
    port: int = 6667,
    verbose=True,
):
    "a functional interface to pushing a message"
    tstamp = tstamp or local_clock()
    payload = Payload(fmt, msg, tstamp)
    try:
        Client(host=host, port=port, verbose=verbose).push(payload)
        return True
    except (ConnectionRefusedError, ConnectionResetError) as e:
        if verbose and msg != "ping":  # pragma no cover
            print(e)
            print(f"Localite EXT at {host}:{port} is not available")
        return False


def available(port: int = 6667, host: str = "127.0.0.1") -> bool:
    """test whether EXT is available at port

    args
    ----

    host: str
        the ip of the EXT (defaults to localhost)

    port: int
        the port number of the EXT (defaults to 6667)

    returns
    -------

    status: bool
        True if available, False if not
    """
    return push_payload(Payload("cmd", "ping", local_clock()))


def kill(port: int = 6667, host: str = "127.0.0.1") -> bool:
    """kill the  markerserver is already  at that port

    args
    ----

    host: str
        the ip of the markerserver (defaults to localhost)

    port: int
        the port number of the markerserver (defaults to 6667)

    returns
    -------

    status: bool
        True if message was sent, False if server was not available
    """
    return push_payload(Payload("cmd", "poison-pill", local_clock()))

