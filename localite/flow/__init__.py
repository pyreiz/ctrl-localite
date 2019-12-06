from typing import NewType, Dict, Union, Tuple

TimeStamp = Union[int, None]
Message = NewType("Message", Dict[str, str])
Payload = NewType("Payload", Tuple[Message, TimeStamp])


def has_poison(payload: Payload) -> bool:
    "return whether there is a poison-pill in the payload"
    for k, v in payload[0].items():
        if {k.lower(): v.lower()} == {"cmd": "poison-pill"}:
            return True
    return False
