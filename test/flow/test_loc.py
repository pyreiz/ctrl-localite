from pytest import fixture
from localite.flow.loc import LOC, Mock
from localite.flow.payload import Queue
import time

host = "127.0.0.1"
port = 6666


@fixture
def mock():
    mock = Mock(host=host, port=port)
    mock.start()
    mock.await_running()
    yield mock
    mock.kill()
    t0 = time.time()
    d = 0
    while mock.is_running.is_set() and d < 5:
        d = time.time() - t0
    assert d < 6
    assert not mock.is_running.is_set()


@fixture
def loc(capsys):
    inbox = Queue()
    outbox = Queue()
    loc = LOC(host=host, port=port, inbox=inbox, outbox=outbox,)
    yield loc


def test_mock(mock):
    assert mock.is_running.is_set()
