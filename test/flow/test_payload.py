from localite.flow.payload import (
    has_poison,
    Payload,
    Queue,
    get_from_queue,
    put_in_queue,
)


def test_payload_repr():
    self = Payload("mrk", "test")
    other = eval(repr(self))
    assert self == other
    assert self != "test"
    other = Payload("mrk", "other")
    assert self != other

def test_has_poison():
    payload = Payload("cmd", "poison-pill", 12345)
    assert has_poison(payload)


def test_has_no_poison():
    payload = Payload("Cmd", "Poison-Pill", 12345)
    assert not has_poison(payload)
    payload = Payload("cmd", "poisonpill", 12345)
    assert not has_poison(payload)
    payload = Payload("command", "poison-pill", 12345)
    assert not has_poison(payload)


def test_get_no_wait():
    q = Queue()
    payload = Payload("cmd", "test", 12345)
    put_in_queue(payload, q)
    received = get_from_queue(q)
    assert received == payload
    received = get_from_queue(q)
    assert received is None
