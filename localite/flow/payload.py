from typing import NewType, Dict, Union, Tuple
from dataclasses import dataclass
from queue import Queue
import json


TimeStamp = Union[
    int, None
]  #: A TimeStamp, which is usually derived from pylsl.local_clock, but can be None
Message = NewType(
    "Message", Union[str, Dict[str, str]]
)  # : The Message, which can be a dictionary or a simple string


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


def get_no_wait(queue: Queue) -> Union[Payload, None]:
    "get the next item in the queue, or None, if empty"
    from queue import Empty
    from time import sleep

    try:
        payload = queue.get_nowait()
        queue.task_done()
        return payload
    except Empty:
        sleep(0.001)
        return None
