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


def test_coil_raw_request(mock, coil):

    msg = '{"get":"coil_0_temperature"}'
    coil._push_loc(msg=msg)
    assert coil.receiver.await_response(msg)[0] == {"coil_0_temperature": 35}


def test_coil_properties(mock, coil):
    assert coil.target_index == 1
    assert coil.temperature == 35
    assert coil.didt == 99

    coil.trigger()


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

