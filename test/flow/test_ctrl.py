from localite.flow.payload import Queue, Payload, get_from_queue
from localite.flow.ctrl import CTRL
from pytest import fixture
import time


@fixture
def ctrl(capsys):
    queue = Queue()
    loc = Queue()
    mrk = Queue()
    ctrl = CTRL(queue, loc, mrk)
    ctrl.start()
    ctrl.await_running()
    pipe = capsys.readouterr()
    assert "CTRL started" in pipe.out
    assert ctrl.is_running.is_set()
    yield ctrl
    killpayload = Payload("cmd", "poison-pill", 12345)
    ctrl.queue.put(killpayload)
    time.sleep(0.1)
    assert ctrl.is_running.is_set() == False
    pipe = capsys.readouterr()
    assert "Shutting CTRL down" in pipe.out
    locp = ctrl.loc.get_nowait()
    mrkp = ctrl.mrk.get_nowait()
    assert mrkp == killpayload
    assert locp == killpayload


def test_cmd(ctrl, capsys):
    ctrl.queue.put(Payload("cmd", "test", 12345))
    time.sleep(0.1)
    pipe = capsys.readouterr()
    assert "CTRL:CMD" in pipe.out


def test_unknown(ctrl, capsys):
    ctrl.queue.put(Payload("unk", "test", 12345))
    time.sleep(0.1)
    pipe = capsys.readouterr()
    assert "CTRL:FMT" in pipe.out


def test_ping(ctrl, capsys):
    ctrl.queue.put(Payload("cmd", "ping", 12345))
    time.sleep(0.1)
    pipe = capsys.readouterr()
    assert "ping" in pipe.out


def test_forwarding(ctrl, capsys):
    locp = Payload("loc", "test", 12345)
    mrkp = Payload("mrk", "test", 12345)
    ctrl.queue.put(locp)
    ctrl.queue.put(mrkp)
    time.sleep(0.1)
    pipe = capsys.readouterr()
    assert ctrl.loc.get_nowait() == locp
    assert ctrl.mrk.get_nowait() == mrkp


def test_latency_below_1ms(ctrl):
    locp = Payload("loc", "test", 12345)
    ctrl.queue.put(locp)
    t0 = time.time()
    while get_from_queue(ctrl.queue) is None:
        pass
    latency = time.time() - t0
    assert latency < 0.001
