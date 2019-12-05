from pylsl import resolve_streams, resolve_byprop, StreamInlet
from pytest import fixture
import pkg_resources
import time
from localite.client import push, available
import json


def test_markerstreamer(ms, capsys):
    sinfo = resolve_byprop("name", "localite_marker")[0]
    out = str(StreamInlet(sinfo).info().as_xml())
    assert "<name>localite_marker</name>" in out
    assert "<type>Markers</type>" in out
    v = str(
        pkg_resources.get_distribution("localite"))
    assert f"<streamer>{v}</streamer>" in out


def test_direct_queueing(ms, capsys):
    msg = json.dumps({"command": "test"})
    tstamp = None
    ms.push(msg, tstamp)
    time.sleep(0.5)
    out, err = capsys.readouterr()
    assert str(msg) in out
