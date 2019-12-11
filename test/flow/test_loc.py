# from .mock_localite import Mock
from pytest import fixture
from localite.flow.mock import Mock
from localite.flow.loc import LOC, is_valid
from localite.flow.payload import Queue, Payload, put_in_queue, get_from_queue
import time
import json

host = "127.0.0.1"
port = 6666


@fixture(scope="module")
def mock():
    mock = Mock(host=host, port=port)
    mock.start()
    mock.await_running()
    yield mock
    # shut down in less than 7s
    mock.kill()
    t0 = time.time()
    d = 0
    while mock.is_running.is_set() and d < 7:
        d = time.time() - t0
    assert not mock.is_running.is_set()


@fixture(scope="module")
def loc(mock):
    inbox = Queue()
    outbox = Queue()
    loc = LOC(host=host, port=port, inbox=inbox, outbox=outbox)
    loc.start()
    loc.await_running()
    yield loc
    # shut down in less than 7s
    pl = Payload("cmd", "poison-pill", 12345)
    put_in_queue(pl, loc.inbox)
    t0 = time.time()
    d = 0
    while loc.is_running.is_set() and d < 7:
        d = time.time() - t0
    assert not loc.is_running.is_set()


def test_mock_running(mock):
    assert mock.is_running.is_set()


def test_loc_running(loc):
    assert loc.is_running.is_set()


def test_listen(loc, mock):
    t0 = time.time()
    while t0 - time.time() < 5:
        pl = get_from_queue(loc.outbox)
        if pl is not None:
            break
    assert pl.fmt == "mrk"


def test_get(loc, mock):
    msg = json.dumps(
        {
            "coil_0_response": {
                "mepmaxtime": 18,
                "mepamplitude": 50,
                "mepmin": -25,
                "mepmax": 25,
            }
        }
    )
    payload = Payload("loc", msg, 12345)
    put_in_queue(payload, loc.inbox)
    recv = []
    t0 = time.time()
    while t0 - time.time() < 5:
        pl = get_from_queue(loc.outbox)
        if pl is not None:
            recv.append(pl)
            if "coil_0_response" in pl.msg:
                break

    assert pl.fmt == "mrk"
    assert "coil_0_response" in pl.msg


def test_set_response(loc, mock):
    "coil_0_response"
    payload = Payload("loc", '{"get": "coil_0_amplitude"}', 12345)
    put_in_queue(payload, loc.inbox)
    recv = []
    t0 = time.time()
    while t0 - time.time() < 5:
        pl = get_from_queue(loc.outbox)
        if pl is not None:
            recv.append(pl)
            if "coil_0_amplitude" in pl.msg:
                break
    assert "coil_0_amplitude" in pl.msg


def test_invalid(loc, mock):
    pl = Payload("loc", '{"garbage": "garbage"}', 12345)
    put_in_queue(pl, loc.inbox)
    recv = []
    t0 = time.time()
    while t0 - time.time() < 5:
        pl = get_from_queue(loc.outbox)
        if pl is not None:
            recv.append(pl)
            if "garbage" in pl.msg:
                break
    assert "error" in pl.msg


def test_trigger(loc, mock):
    pl = Payload("loc", '{"single_pulse":"COIL_0"}', 12345)
    put_in_queue(pl, loc.inbox)
    recv = []
    t0 = time.time()
    while t0 - time.time() < 5:
        pl = get_from_queue(loc.outbox)
        if pl is not None:
            recv.append(pl)
            if "coil_0_didt" in pl.msg:
                break

    assert "coil_0_didt" in pl.msg


def test_valid():
    def pl(msg: str) -> Payload:
        return Payload(fmt="loc", msg=msg)

    assert not is_valid(Payload(fmt="mrk", msg='{"get":"test_xase"}'))
    assert not is_valid(pl('{"get":"test_xase"}'))
    assert is_valid(pl('{"get":"pointer_position"}'))
    assert is_valid(
        pl(
            '{"coil_0_response": {"mepmaxtime": 25, "mepamplitude": 50, "mepmin": -25, "mepmax": 25} }'
        )
    )
    assert (
        is_valid(
            pl(
                '{"coil_0_response": {"mepmaxtime": -1, "mepamplitude": 50, "mepmin": -25, "mepmax": 25} }'
            )
        )
        == False
    )
    assert (
        is_valid(
            pl(
                '{"coil_0_response": {"mepmaxtime": 25, "mepamplitude": 50, "garbage": -25, "mepmax": 25} }'
            )
        )
        == False
    )
    assert (
        is_valid(
            pl(
                '{"coil_0_response": {"mepmaxtime": 25, "mepamplitude": 50, "mepmin": -25, "mepmax": 999999999} }'
            )
        )
        == False
    )
    assert is_valid(pl('{"single_pulse":"COIL_0"}'))
    assert is_valid(pl('{"coil_0_amplitude": 20}'))
    assert is_valid(pl('{"coil_0_amplitude": -1}')) == False
    assert is_valid(pl('{"coil_0_target_index": 20}'))
    assert is_valid(pl('{"coil_0_target_index": -1}')) == False
    assert is_valid(pl('{"current_instrument": "POINTER"}'))
    assert is_valid(pl('{"garbage": "garbage"}')) == False
