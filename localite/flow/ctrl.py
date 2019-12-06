import threading
from localite.flow.payload import Queue, get_no_wait


class CTRL(threading.Thread):
    def __init__(self, queue: Queue):
        threading.Thread.__init__(self)
        self.is_running = threading.Event()
        self.queue = queue

    def run(self):
        self.is_running.set()
        print("CTRL started")
        while self.is_running.is_set():
            payload = get_no_wait(self.queue)
            if payload is None:
                continue
            print(f"Received {payload} in CTRL")
            if payload.fmt == "cmd":
                pass
            elif payload.fmt == "loc":
                pass
            elif payload.fmt == "mrk":
                pass
            else:
                print("Unknown msg format: {0}".format(payload.fmt))
        print("Shutting CTRL down")
