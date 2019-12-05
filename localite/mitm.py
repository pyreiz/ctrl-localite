from pylsl import StreamInfo, StreamOutlet
import pylsl
import socket
import threading
import queue
import json
from time import sleep
import pkg_resources
from localite.local import available

# -----------------------------------------------------------------------------
def _read_msg(client):
    "receive byte for byte to read the header telling the message length"
    # parse the message until it is a valid json
    msg = bytearray(b" ")
    while True:
        try:
            prt = client.recv(1)
            msg += prt
            # because the first byte is b' '
            marker, tstamp = json.loads(msg.decode("ascii"))
            print(f"Received {marker} for {tstamp} at {pylsl.local_clock()}")
            return marker, tstamp
        except json.decoder.JSONDecodeError:
            pass
        except Exception as e:
            print(e)
            break

    return ("", None)


class ManInTheMiddle(threading.Thread):
    """Main class to manage the LSL-MarkerStream as man-in-the-middle

    when started, it automatically checks whether there is already a MarkerServer
    running at that port. If this is the case, it returns and lets the old one
    keep control. This ensures that subscribers to the old MarkerServer
    don't experience any hiccups.
    """

    def __init__(
        self,
        name="localite_marker",
        own_host: str = "127.0.0.1",
        own_port: int = 6667,
        localite_host: str = "127.0.0.1",
        localite_port: int = 6666,
    ):
        threading.Thread.__init__(self)
        self.name = name
        self.localite_host = localite_host
        self.localite_port = localite_port
        self.host = own_host
        self.port = own_port
        self.is_running = threading.Event()
        self.is_running.clear()
        self.singleton = threading.Event()

    def stop(self):
        "stop the server"
        self.is_running.clear()

    def await_running(self):
        print("[", end="")
        while not self.is_running.is_set():
            print(".", end="")
            sleep(0.5)
        print("]")

    def run(self):
        """wait for clients to connect and send messages.

        This is a Thread, so start with :meth:`server.start`
        """

        # we check whether there is already an instance running, and if so
        # let it keep control by returning
        if available(self.port):
            self.singleton.clear()
            print("Server already running on that port")
            self.is_running.set()
            return
        else:
            self.singleton.set()
            print("This server is the original instance")

        # create the MarkerStreamer, i.e. the LSL-Server that distributes the
        # strings received from the Listener
        markerstreamer = MarkerStreamer(name=self.name)
        markerstreamer.start()
        # create the ListenerServer, i.e. the TCP/IP Server that waits for
        # messages for forwarding them to the MarkerStreamer
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.settimeout(1)
        listener.bind((self.host, self.port))
        listener.listen(1)
        print(
            "Server mediating an LSL Outlet opened at {0}:{1}".format(
                self.host, self.port
            )
        )

        markerstreamer.await_running()
        self.is_running.set()
        while self.is_running.is_set():
            try:
                client, address = listener.accept()
                try:
                    msg, tstamp = _read_msg(client)
                    ping, poison = False, False
                    for k, v in msg.items():
                        if k == "cmd" and v.lower() == "ping":
                            ping = True
                        elif k == "cmd" and v.lower() == "poison-pill":
                            poison = True
                    if ping:
                        print("Received ping from", address)
                        continue
                    if poison:
                        print("Swallowing poison pill")
                        self.is_running.clear()
                        break
                    markerstreamer.push(json.dumps(msg), tstamp)
                except socket.timeout:
                    print("Client from {address} timed out")
                finally:
                    client.shutdown(2)
                    client.close()
            except socket.timeout:
                pass

        print(f"Shutting down MarkerServer: {self.name}")
        markerstreamer.stop()


# ------------------------------------------------------------------------------
def create_outlet(name: str = "localite_markers") -> [StreamOutlet, StreamInfo]:
    """Create a Marker StreamOutlet with the given name.

    Raise an ConnectionAbortedError if the source_id is already in use somewhere else

    """
    source_id = "_".join((socket.gethostname(), name))
    info = StreamInfo(
        name,
        type="Markers",
        channel_count=1,
        nominal_srate=0,
        channel_format="string",
        source_id=source_id,
    )

    info.desc().append_child_value("software", "localite TMS Navigator 4.0")
    info.desc().append_child_value("stimulator", "MagVenture")
    info.desc().append_child_value(
        "streamer", str(pkg_resources.get_distribution("localite"))
    )

    outlet = StreamOutlet(info)
    return outlet, info


class MarkerStreamer(threading.Thread):
    "publishes whatever is in its queue as a MarkerStream"

    def __init__(self, name: str = "localite_marker"):
        threading.Thread.__init__(self)
        self.queue = queue.Queue(maxsize=0)  # indefinite size
        self.is_running = threading.Event()
        self.name = name

    def push(self, marker: str = "", tstamp: float = None):
        if marker == "":
            return
        if tstamp is None:
            tstamp = pylsl.local_clock()
        self.queue.put_nowait((marker, tstamp))

    def stop(self):
        self.queue.join()
        self.is_running.clear()

    def await_running(self):
        print("[", end="")
        while not self.is_running.is_set():
            print(".", end="")
            sleep(0.5)
        print("]")

    def run(self):
        try:
            outlet, info = create_outlet(name=self.name)
        except ConnectionAbortedError as e:
            print(e)
            return
        print("Starting MarkerStreamer")
        print(info.as_xml())
        self.is_running.set()
        while self.is_running.is_set():
            try:
                marker, tstamp = self.queue.get(block=False)
                outlet.push_sample([marker], tstamp)
                self.queue.task_done()
                print(f"Pushed {marker} from {tstamp} at {pylsl.local_clock()}")
            except queue.Empty:
                sleep(0.001)
        print(f"Shutting down MarkerStreamer: {self.name}")
