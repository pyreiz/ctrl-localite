from typing import NewType, Dict, Union, Tuple
from dataclasses import dataclass
from queue import Queue
import json


TimeStamp = Union[
    int, None
]  #: A TimeStamp, which is usually derived from pylsl.local_clock, but can be None
Message = NewType(
    "Message", str
)  # : The Message, which can be e.g.  json-dumped variable or a plain string


@dataclass
class Payload:
    fmt: str = ""
    msg: Message = ""
    tstamp: TimeStamp = None


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
