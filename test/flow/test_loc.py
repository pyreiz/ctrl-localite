from .mock_localite import Mock
from pytest import fixture
from localite.flow.loc import LOC, localiteClient, json, is_valid
from localite.flow.payload import Queue, Payload, put_in_queue, get_from_queue
import time


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


def test_get(loc, mock, capsys):
    payload = Payload("loc", '{"get": "coil_0_amplitude"}', 12345)
    put_in_queue(payload, loc.inbox)
    time.sleep(0.5)
    recv = []
    while loc.outbox.unfinished_tasks:
        pl = get_from_queue(loc.outbox)
        recv.append(pl)
        if "property" in pl.msg:
            break

    assert pl.fmt == "mrk"
    assert pl.msg == '{"coil_0_amplitude": "answer"}'


def test_invalid(loc, mock, capsys):
    pipe = capsys.readouterr()
    pl = Payload("loc", '{"garbage": "garbage"}', 12345)
    put_in_queue(pl, loc.inbox)
    time.sleep(1)
    pipe = capsys.readouterr()
    assert "LOC:INVALID" in pipe.out


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
