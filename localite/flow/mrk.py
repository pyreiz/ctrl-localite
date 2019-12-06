from pylsl import StreamInfo, StreamOutlet, local_clock
from localite.flow.payload import Queue, get_from_queue
import socket
import pkg_resources
import datetime
import threading
import time


def make_outlet(name="localite_marker") -> [StreamOutlet, StreamInfo]:
    source_id = "_at_".join((name, socket.gethostname()))
    info = StreamInfo(
        name,
        type="Marker",
        channel_count=1,
        nominal_srate=0,
        channel_format="string",
        source_id=source_id,
    )

    d = info.desc()
    d.append_child_value("version", str(pkg_resources.get_distribution("localite")))
    d.append_child_value("datetime", str(datetime.datetime.now()))
    d.append_child_value("hostname", str(socket.gethostname()))
    outlet = StreamOutlet(info)
    return outlet, info


class MRK(threading.Thread):
    def __init__(self, mrk: Queue):
        threading.Thread.__init__(self)
        self.is_running = threading.Event()
        self.queue = mrk

    def await_running(self):
        while not self.is_running.is_set():
            pass

    def run(self):
        outlet, info = make_outlet()
        print(info.as_xml())
        self.is_running.set()
        while self.is_running.is_set():
            payload = get_from_queue(self.queue)
            if payload is None:
                time.sleep(0.001)
                continue
            if payload.fmt == "cmd" and payload.msg == "poison-pill":
                self.is_running.clear()
                outlet.push_sample([payload.msg])
                break

            outlet.push_sample([str(payload.msg)], payload.tstamp)
            latency = 1000 * (payload.tstamp - local_clock())
            print(
                f"{datetime.datetime.now()}: Pushed {payload.msg} from {payload.tstamp} delayed by {latency:1.2f}ms"
            )

        print("Shutting MRK down")
