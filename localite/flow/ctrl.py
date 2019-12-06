import threading
from localite.flow.payload import Queue, get_from_queue, has_poison, put_in_queue
from time import sleep


class CTRL(threading.Thread):
    def __init__(self, queue: Queue, loc: Queue, mrk: Queue):
        threading.Thread.__init__(self)
        self.is_running = threading.Event()
        self.queue = queue
        self.loc = loc
        self.mrk = mrk

    def await_running(self):
        while not self.is_running.is_set():
            pass

    def run(self):
        self.is_running.set()
        print("CTRL started")
        while self.is_running.is_set():
            payload = get_from_queue(self.queue)
            if payload is None:
                sleep(0.001)
                continue
            print(f"Received {payload} in CTRL")
            if payload.fmt == "cmd":
                if has_poison(payload):
                    put_in_queue(payload, self.loc)
                    put_in_queue(payload, self.mrk)
                    self.is_running.clear()
                    break
                else:
                    print("Unknown cmd: {0}".format(payload.msg))
            elif payload.fmt == "loc":
                put_in_queue(payload, self.loc)
            elif payload.fmt == "mrk":
                put_in_queue(payload, self.mrk)
            else:
                print("Unknown fmt: {0}".format(payload.fmt))
        print("Shutting CTRL down")