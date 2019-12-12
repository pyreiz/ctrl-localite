import os
from pytest import fixture
from localite.coil import Coil
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
    coil.push_loc(msg=msg)
    assert coil.receiver.await_response(msg)[0] == {"coil_0_temperature": 35}

    msg = '{"single_pulse":"COIL_0"}'
    coil.push_loc(msg=msg)
    assert coil.receiver.await_response(msg)[0] == {"coil_0_didt": 11}

    msg = '{"coil_0_amplitude": 10}'
    coil.push_loc(msg=msg)
    assert coil.receiver.await_response(msg)[0] == {"coil_0_amplitude": 10}


if "LOCALITE_HOST" in os.environ:
    import time

