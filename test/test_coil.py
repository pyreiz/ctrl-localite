import os
from pytest import fixture, raises
from localite.coil import Coil, pythonize_response
from subprocess import Popen
import time


@fixture(scope="module")
def mock():
    Popen(["localite-mock"])
    yield True
    Popen(["localite-mock", "--kill"])


@fixture(scope="module")
def coil():
    coil = Coil()
    yield coil
    coil.receiver.stop()


def test_get_coil_temperature(mock, coil):

    msg = '{"get":"coil_0_temperature"}'
    coil._push_loc(msg=msg)
    assert coil.receiver.await_response(msg)[0] == {"coil_0_temperature": 35}

    msg = '{"single_pulse":"COIL_0"}'
    coil._push_loc(msg=msg)
    assert coil.receiver.await_response(msg)[0] == {"coil_0_didt": 11}

    msg = '{"coil_0_amplitude": 10}'
    coil._push_loc(msg=msg)
    assert coil.receiver.await_response(msg)[0] == {"coil_0_amplitude": 10}


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


def test_properties(coil, mock):
    assert coil.connected == True
    with raises(AttributeError):
        coil.connected = False

    assert coil.id == "0"


if "LOCALITE_HOST" in os.environ:
    import time

