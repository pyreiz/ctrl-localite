from localite.flow.mock import append, Queue, mocked_settings
from localite.flow.mock import create_response as cr
import threading
import time
from subprocess import Popen, PIPE
import pytest


def test_message_queue():
    outqueue = Queue(maxsize=7)
    is_running = threading.Event()
    appender = threading.Thread(target=append, args=(outqueue, is_running, 0.1))
    appender.start()
    is_running.set()
    time.sleep(2)
    is_running.clear()
    assert outqueue.unfinished_tasks == 7


def test_cli():
    p = Popen(["localite-mock"], stderr=PIPE, stdout=PIPE)
    time.sleep(1)
    Popen(["localite-mock", "--kill"])
    time.sleep(1)
    o, e = p.communicate()
    assert b"Shutting MOCK down" in o


def test_create_response():
    assert cr(None) == None
    assert "error" in cr({"current_instrument": "GARBAGE"}).keys()
    assert "NONE" in cr({"current_instrument": "NONE"}).values()
    assert 1 in cr({"coil_0_target_index": 1}).values()
    assert "error" in cr({"coil_0_target_index": -1}).keys()
    assert "error" in cr({"coil_0_target_index": "T"}).keys()
    assert "coil_0_didt" in cr({"single_pulse": "COIL_0"}).keys()
    assert "error" in cr({"single_pulse": "COIL_2"}).keys()
    assert 1 in cr({"coil_0_amplitude": 1}).values()
    assert "error" in cr({"coil_0_amplitude": -1}).keys()
    rsp = {"mepmaxtime": 18, "mepamplitude": 50, "mepmin": -25, "mepmax": 25}
    assert rsp in cr({"coil_0_response": rsp}).values()
    bad = {"mepmaxtime": -99999, "mepamplitude": 50, "mepmin": -25, "mepmax": 25}
    assert "error" in cr({"coil_0_response": bad}).keys()
    bad = {"mepmaxtime": 18, "mepamplitude": -99999, "mepmin": -25, "mepmax": 25}
    assert "error" in cr({"coil_0_response": bad}).keys()
    assert "error" in cr({"bad": "bad"}).keys()
    assert "error" in cr({"get": "bad"}).keys()


prms = [(k, v) for k, v in mocked_settings.items()]


@pytest.mark.parametrize("k, v", prms)
def test_get_response(k, v):
    assert cr({"get": k})[k] == v

