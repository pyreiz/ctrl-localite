from pytest import fixture
from .mock_localite import Mock
from localite.flow.loc import LOC, localiteClient, json
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
    payload = Payload("loc", '{"get": "property"}', 12345)
    put_in_queue(payload, loc.inbox)
    time.sleep(0.5)
    recv = []
    while loc.outbox.unfinished_tasks:
        pl = get_from_queue(loc.outbox)
        recv.append(pl)
        if "property" in pl.msg:
            break

    assert pl.fmt == "mrk"
    assert pl.msg == '{"property": "answer"}'
    assert json.loads(pl.msg) == {"property": "answer"}


def test_set(loc, mock, capsys):
    pl = Payload("loc", '{"set": "test"}', 12345)
    put_in_queue(pl, loc.inbox)

