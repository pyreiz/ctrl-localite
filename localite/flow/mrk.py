from pylsl import StreamInfo, StreamInlet, StreamOutlet, local_clock, resolve_stream
import json
from localite.flow.payload import Queue, get_from_queue
import socket
import pkg_resources
import datetime
import threading
import time
from typing import Tuple, Any, List
from collections import deque
import queue


class Buffer:
    def __init__(self):
        self.queue = queue.Queue()

    def put(self, item: Any):
        "put a new item in the buffer"
        self.queue.put(item)

    def get_as_list(self) -> List[Any]:
        "empty the buffer and return content as a list"
        content = []
        while True:
            try:
                item = self.queue.get_nowait()
                self.queue.task_done()
                content.append(item)
            except queue.Empty:
                return content


def expectation(msg: str) -> str:
    msg = json.loads(msg)
    key = list(msg.keys())[0]
    if key == "get":
        return msg["get"]
    elif "single_pulse" in key:
        return msg["single_pulse"].lower() + "_didt"
    else:
        return key


class Receiver(threading.Thread):
    def __init__(self, name="localite_marker"):
        threading.Thread.__init__(self)
        self.name = name
        self.buffer = Buffer()
        self.is_running = threading.Event()

    def clear(self):
        [i for i in self.buffer.get_as_list()]

    def await_response(self, msg: str):
        key = expectation(msg)
        while True:
            content = self.content
            for item in content:
                if key in item[0][0]:
                    return json.loads(item[0][0]), item[1]
            time.sleep(0.01)

    @property
    def content(self) -> List[Any]:
        return self.buffer.get_as_list()

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
