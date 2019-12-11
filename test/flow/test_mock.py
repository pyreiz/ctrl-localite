from localite.flow.mock import append, Queue
import threading
import time
from subprocess import Popen, PIPE


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
    o, e = p.communicate()
    assert b"Shutting MOCK down" in o
