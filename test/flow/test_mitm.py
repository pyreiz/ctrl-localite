# from .mock_localite import Mock
from localite.flow.mock import Mock
from localite.flow.mitm import start_threaded, start, kill
import time
from pytest import fixture
from subprocess import Popen, PIPE


@fixture(scope="module")
def mock():
    host = "127.0.0.1"
    port = 6666
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


def test_setup_tear_down(mock, capsys):
    start_threaded(loc_host="127.0.0.1")
    kill()
    time.sleep(1)
    pipe = capsys.readouterr()
    assert "Shutting EXT down" in pipe.out
    assert "Shutting CTRL down" in pipe.out
    assert "Shutting MRK down" in pipe.out
    assert "Shutting LOC down" in pipe.out


def test_cli(mock):
    p = start(host="127.0.0.1")
    time.sleep(1)
    o, e = Popen(["localite-flow", "--kill"], stdout=PIPE).communicate()
    assert b"poison-pill" in o

    o, e = p.communicate()
    time.sleep(1)
    assert b"[Errno 111] Connection refused" not in o


def test_cli_help():
    out = Popen(["localite-flow"], stdout=PIPE)
    o, e = out.communicate()
    assert b"usage: localite-flow [-h]" in o
