from pytest import fixture
import time
from localite.client import available


@fixture(scope="module")
def ms():
    from localite.mitm import MarkerStreamer
    ms = MarkerStreamer()
    t0 = time.time()
    ms.start()
    ms.await_running()
    assert (time.time()-t0) < 5  # start within 5 seconds
    assert ms.is_running.is_set()
    yield ms
    ms.stop()
    time.sleep(1)  # shut down within one second
    assert ms.is_running.is_set() == False
