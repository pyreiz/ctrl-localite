from localite.mitm import MarkerStreamer, create_outlet
from pylsl import resolve_streams
from pytest import fixture
import pkg_resources
import time


@fixture
def ms(capsys):
    ms = MarkerStreamer()
    yield ms
    ms.stop()
    time.sleep(1)  # shut down within one second
    out, err = capsys.readouterr()
    assert "Shutting down" in out


def test_markerstreamer(ms, capsys):
    t0 = time.time()
    ms.start()
    ms.await_running()
    assert (time.time()-t0) < 5  # start within 5 seconds
    out, err = capsys.readouterr()
    assert "<name>localite_marker</name>" in out
    assert "<type>Markers</type>" in out
    v = str(
        pkg_resources.get_distribution("localite"))
    assert f"<streamer>{v}</streamer>" in out
