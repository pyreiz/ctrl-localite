import threading
from localite.flow.payload import (
    Queue,
    get_from_queue,
    has_poison,
    put_in_queue,
    has_ping,
)
from time import sleep


class CTRL(threading.Thread):
    def __init__(self, queue: Queue, loc: Queue, mrk: Queue):
        threading.Thread.__init__(self)
        self.is_running = threading.Event()
        self.queue = queue
        self.loc = loc
        self.mrk = mrk

    def await_running(self):
        while not self.is_running.is_set():  # pragma no cover
            pass

    def run(self):
        self.is_running.set()
        print("CTRL started")
        while self.is_running.is_set():
            payload = get_from_queue(self.queue)
            if payload is None:
                sleep(0.001)
                continue
            print(f"CTRL:RECV {payload}")
            if payload.fmt == "cmd":
                if has_poison(payload):
                    put_in_queue(payload, self.loc)
                    put_in_queue(payload, self.mrk)
                    self.is_running.clear()
                    break
                elif has_ping(payload):
                    continue
                else:
                    print("CTRL:CMD {0} unknown".format(payload.msg))
            elif payload.fmt == "loc":
                put_in_queue(payload, self.loc)
            elif payload.fmt == "mrk":
                put_in_queue(payload, self.mrk)
            else:
                print("CTRL:FMT {0} fmt".format(payload.fmt))
        print("Shutting CTRL down")
