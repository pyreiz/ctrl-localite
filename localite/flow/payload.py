from typing import NewType, Dict, Union, Tuple
from queue import Queue
import json
from pylsl import local_clock

TimeStamp = Union[
    int, None
]  #: A TimeStamp, which is usually derived from pylsl.local_clock, but can be None
Message = (
    str  # : The Message, which can be e.g.  json-dumped variable or a plain string
)


class Payload:
    def __init__(self, fmt: str = "", msg: str = "", tstamp: TimeStamp = None):
        self.fmt = fmt
        self.msg = msg
        self.tstamp = tstamp or local_clock()

    def __str__(self):
        return str(self.fmt) + " " + str(self.msg) + " @ " + f"{self.tstamp:.5f}"

    def __repr__(self):
        return f"Payload('{self.fmt}', '{self.msg}', {self.tstamp})"

    def __eq__(self, other):
        if isinstance(other, Payload):
            return all((self.fmt == other.fmt, self.msg == other.msg, self.tstamp == other.tstamp))
        else:
            return False

def has_poison(payload: Payload) -> bool:
    "return whether there is a poison-pill in the Payload"
    if (payload.fmt, payload.msg) == ("cmd", "poison-pill"):
        return True
    else:
        return False


def has_ping(payload: Payload) -> bool:
    "return whether there is a ping in the Payload"
    return True if (payload.fmt, payload.msg) == ("cmd", "ping") else False


def get_from_queue(queue: Queue) -> Union[Payload, None]:
    "get the next item in the queue, or None, if empty"
    from queue import Empty

    try:
        payload = queue.get_nowait()
        queue.task_done()
        return payload
    except Empty:
        return None


def put_in_queue(payload: Payload, queue: Queue) -> None:
    "put the next item in the queue"
    queue.put(payload)
