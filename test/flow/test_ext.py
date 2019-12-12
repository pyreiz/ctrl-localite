from pytest import fixture
from localite.flow.ext import EXT, read_msg, available, kill, push
from localite.flow.payload import Queue
import time


@fixture
def queue():
    queue = Queue()
    yield queue


@fixture
def ext(queue, capsys):
    assert available() == False
    ext = EXT(queue=queue)
    ext.start()
    ext.await_running()
    assert available()
    yield ext
    kill()
    while ext.is_running.is_set():
        pass
    time.sleep(0.1)
    assert not available()
    time.sleep(0.1)
    out, err = capsys.readouterr()
    assert "poison-pill" in out
    assert "Shutting EXT down" in out
    assert kill() == False
    assert push("cmd", "ping") == False


def test_push(ext, capsys):
    assert ext.is_running.is_set() == True
    push("cmd", "ping")
    out, err = capsys.readouterr()
    assert "PUSH" in out
    assert push("wrong", "ping") == True
    time.sleep(0.1)
    out, err = capsys.readouterr()
    assert "is no valid Payload" in out
