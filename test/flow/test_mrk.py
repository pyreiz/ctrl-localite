from pytest import fixture
from localite.flow.mrk import MRK, Buffer, Receiver
from localite.flow.payload import Queue, Payload
import time
import pylsl
import threading


def test_buffer():
    b = Buffer()
    inp = [1, 2, 3, 4, 5]
    for i in inp:
        b.put(i)
    out = [i for i in b]
    assert inp == out


def test_receiver():
    outlet = pylsl.StreamOutlet(
        pylsl.StreamInfo(
            name="test_marker",
            type="Marker",
            channel_count=1,
            nominal_srate=0,
            channel_format="string",
        )
    )
    r = Receiver(name="test_marker")
    #    r = Receiver(name="Liesl-Mock-Marker")
    r.start()
    time.sleep(5)

    inp = ["1", "2", "3", "4", "5"]
    for i in inp:
        outlet.push_sample([i])
    time.sleep(0.1)
    out = [i[0][0] for i in r]
    assert inp == out
    inp = ["1", "2", "3", "4", "5"]
    for i in inp:
        outlet.push_sample([i])
    time.sleep(0.1)
    r.clear()
    out = [i[0][0] for i in r]
    assert out == []


@fixture
def mrk(capsys):
    mrk = Queue()
    mrk = MRK(mrk)
    mrk.start()
    mrk.await_running()
    pipe = capsys.readouterr()
    assert "localite_marker" in pipe.out
    yield mrk
    killpayload = Payload("cmd", "poison-pill", 12345)
    mrk.queue.put(killpayload)
    time.sleep(0.5)
    pipe = capsys.readouterr()
    assert "Shutting MRK down" in pipe.out


def test_latency_below_1ms(mrk, capsys):
    pl = Payload("mrk", "test_latency", pylsl.local_clock())
    mrk.queue.put(pl)
    time.sleep(0.01)
    pipe = capsys.readouterr()
    latency = pipe.out.split("delayed by ")[1].split("ms")[0]
    assert float(latency) < 0.001


def test_sending_out(mrk):
    from os import environ

    if (
        "GITHUB_ACTION" in environ.keys()
    ):  # the LSL sending seems to deadlock on their server
        return

    class Listener(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.running = False

        def run(self):
            sinfo = pylsl.resolve_byprop("name", "localite_marker")[0]
            stream = pylsl.StreamInlet(sinfo)
            msg = []
            time.sleep(1)
            msg, t1 = stream.pull_chunk()
            self.running = True
            while self.running:
                msg, t1 = stream.pull_chunk()
                print(msg)
                if msg == []:
                    time.sleep(0.001)
                else:
                    self.running = False
            self.msg = msg
            self.t1 = t1
            del stream

    l = Listener()
    l.start()
    while not l.running:
        pass
    t0 = pylsl.local_clock()
    pl = Payload("mrk", '{"test":"sending_out"}', t0)
    mrk.queue.put(pl)
    while l.running:
        pass
    assert abs(l.t1[0] - t0) < 0.001
    assert l.msg[0][0] == pl.msg
    l.running = False
