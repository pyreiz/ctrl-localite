from pytest import raises, fixture
from localite.coil import pythonize_response
from localite.coil import Coil
from subprocess import Popen, PIPE
import time
import sys


def test_pythonize():
    msg = {"key": "TRUE"}
    assert pythonize_response(msg) is True
    msg = {"key": "FALSE"}
    assert pythonize_response(msg) is False
    msg = {"key": "None"}
    assert pythonize_response(msg) is None
    msg = {"key": "AnythingElse"}
    assert pythonize_response(msg) == msg["key"]
    msg = {"key": {"subkey": "subvalue"}}
    assert pythonize_response(msg) == msg["key"]


if "win" not in sys.platform:

    @fixture(scope="module")
    def mock():
        p = Popen(["localite-mock"], stderr=PIPE, stdout=PIPE)
        time.sleep(1)
        yield True
        Popen(["localite-mock", "--kill"])
        time.sleep(1)
        o, e = p.communicate()
        assert b"Shutting MOCK down" in o

    @fixture(scope="module")
    def coil(mock):
        coil = Coil()
        yield coil
        coil.receiver.stop()

    def test_coil_raw_request(coil):

        msg = '{"get":"coil_0_temperature"}'
        coil._push_loc(msg=msg)
        assert coil.receiver.await_response(msg)[0] == {"coil_0_temperature": 35}

    def test_coil_static_properties(coil):
        assert coil.waveform == "mockphasic"
        assert coil.mode == "mock"
        assert coil.temperature == 35
        assert coil.didt == 99
        assert coil.visible
        assert coil.connected == True
        with raises(AttributeError):
            coil.connected = False
        assert coil.model == "Mock0704 mock"

    def test_coil_setable_properties(coil):
        assert coil.target_index == 1
        coil.target_index = 2
        coil.target_index = -1
        assert (coil.amplitude == 2) == False
        assert coil.amplitude == 1
        coil.amplitude = 0
        coil.amplitude = -1
        response = coil.position
        expected = {
            "q0": 17.0,
            "qx": 17.0,
            "qy": 17.0,
            "qz": 17.0,
            "x": 37,
            "y": 77,
            "z": 53,
        }
        for k in response:
            assert abs(response[k] - expected[k]) < 0.001

        assert coil.id == "0"
        with raises(ValueError):
            coil.id = -1

    def test_coil_trigger(coil):
        coil.trigger()

    def test_stream_info(coil):
        coil.push_marker("this is a test")
        coil.stream_info()

