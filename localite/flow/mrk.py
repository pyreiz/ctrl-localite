from pylsl import StreamInfo, StreamInlet, StreamOutlet, local_clock, resolve_stream
from localite.flow.payload import Queue, get_from_queue
import socket
import pkg_resources
import datetime
import threading
import time
from typing import Tuple, Any
from collections import deque


class Buffer:
    def __init__(self):
        self.queue = deque()

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return self.queue.pop()
        except IndexError:
            raise StopIteration

    def clear(self):
        self.queue.clear()

    def put(self, item: Any):
        self.queue.appendleft(item)


class Receiver(threading.Thread):
    def __init__(self, name="localite_marker"):
        threading.Thread.__init__(self)
        self.name = name
        self.buffer = Buffer()
        self.is_running = threading.Event()

    def __iter__(self):
        return iter(self.buffer)

    def clear(self):
        self.buffer.clear()

    def run(self):
        sinfo = resolve_stream("name", self.name)[0]
        inlet = StreamInlet(sinfo)
        inlet.pull_chunk()
        self.is_running.set()
        while self.is_running.is_set():
            try:
                mrk, tstamp = inlet.pull_chunk()
                for m, z in zip(mrk, tstamp):
                    if m != []:
                        self.buffer.put((m, z))
            except Exception as e:  # pragma no cover
                print(e)
                self.stop()
        inlet.close_stream()
        del inlet
        print("LSL Receiver shuts down")

    def stop(self):
        self.is_running.clear()


def make_outlet(name="localite_marker") -> Tuple[StreamOutlet, StreamInfo]:
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
        # print(info.as_xml())
        print(f"MRK {info.name()} started")
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
                f"MRK:PUSH {payload.msg} from {payload.tstamp:.5f} delayed by {latency:1.2f}ms"
            )

        print("Shutting MRK down")
