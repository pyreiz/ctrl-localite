from pytest import fixture
import time
from localite.local import available, kill
from localite.mitm import ManInTheMiddle
from localite.mitm import MarkerStreamer


@fixture(scope="module")
def ms():
    ms = MarkerStreamer()
    t0 = time.time()
    ms.start()
    ms.await_running()
    assert (time.time() - t0) < 5  # start within 5 seconds
    assert ms.is_running.is_set()
    yield ms
    ms.stop()
    time.sleep(1)  # shut down within one second
    assert ms.is_running.is_set() == False


@fixture(scope="session")
def mitm():
    mitm = ManInTheMiddle()
    t0 = time.time()
    mitm.start()
    mitm.await_running()
    assert (time.time() - t0) < 5  # start within 5 seconds
    assert mitm.is_running.is_set()
    yield mitm
    kill()
    time.sleep(1)  # shut down within one second
    assert mitm.is_running.is_set() == False

