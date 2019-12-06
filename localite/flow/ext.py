import socket
import threading
import json
from localite.flow.payload import Payload, has_poison, has_ping, Queue
from pylsl import local_clock
from typing import Dict, Any
from subprocess import Popen

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
        while self.is_running.is_set():
            try:
                client, address = listener.accept()
                payload = read_msg(client)
                print(f"Received {payload} from {address}")
                if not payload or has_ping(payload):
                    continue
                self.queue.put(payload)
                if has_poison(payload):
                    self.is_running.clear()
                    break
            except Exception as e:  # pragma no cover
                print(e)
            finally:
                client.shutdown(socket.SHUT_RDWR)
                client.close()
        print("Shutting EXT down")


def read_msg(client: socket.socket) -> Payload:
    """parse the message until it is a valid Payload and return the first"""
    msg = bytearray(b" ")
    while True:
        try:
            prt = client.recv(1)
            msg += prt
            marker, tstamp = json.loads(msg.decode("ascii"))
            for k, v in marker.items():
                # returns only the first cmd-message!
                payload = Payload(k.lower(), v, tstamp)
                return payload

        except json.decoder.JSONDecodeError:
            pass
        except Exception as e:  # pragma no cover
            print(e)
            return None


# ------------------------------------------------------------------------------
class Client:
    "Basic Client communicating with the MarkerServer"

    def __init__(self, host="127.0.0.1", port: int = 6667, verbose=True):
        self.host = host
        self.port = port
        self.verbose = verbose

    def push(self, marker: Dict[str, Any] = {"command": "ping"}, tstamp: float = None):
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


def start():
    "Start the Localite-ManInTheMiddle as an independent process"
    Popen(["ctrl-localite"])


def push(
    marker: Dict[str, Any] = {"command": "ping"},
    tstamp: float = None,
    host="127.0.0.1",
    port: int = 6667,
    verbose=True,
):
    "a functional interface to pushing a message"
    Client(host=host, port=port, verbose=verbose).push(marker, tstamp)


def available(port: int = 6667, host: str = "127.0.0.1", verbose=True) -> bool:
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
    c = Client(host=host, port=port)
    try:
        c.push({"cmd": "ping"}, local_clock())
        return True
    except (ConnectionRefusedError, ConnectionResetError) as e:
        if verbose:  # pragma no cover
            print(e)
            print(f"Markerserver at {host}:{port} is not available")
        return False


def kill(port: int = 6667, host: str = "127.0.0.1", verbose=True) -> bool:
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
    c = Client(host=host, port=port)
    try:
        c.push({"cmd": "poison-pill"}, local_clock())
        return True
    except ConnectionRefusedError as e:
        if verbose:
            print(e)
            print(f"Markerserver at {host}:{port} is not available")
        return False

