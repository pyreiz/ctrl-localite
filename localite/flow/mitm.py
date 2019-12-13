from localite.flow.ext import EXT
from localite.flow.loc import LOC
from localite.flow.mrk import MRK
from localite.flow.ctrl import CTRL
from localite.flow.payload import Queue
from localite.flow.ext import push
from subprocess import Popen, PIPE
import time
from typing import Tuple


def start_threaded(
    loc_host: str, loc_port: int = 6666, address: Tuple[str, int] = ("127.0.0.1", 6667)
):
    """starts the whole flow-pipeline as threads within the local process

    args
    ----
    loc_host: str
        the ip-adress of the localite PC
    loc_port: int = 6666
        the port of the localite Server
    ext: Tuple[str, int] = ("127.0.0.1", 6667)
        the host:port where the localite-flow server will be setup    
    """
    queue = Queue()
    locbox = Queue()
    mrkbox = Queue()
    ext = EXT(host=address[0], port=address[1], queue=queue)
    ctrl = CTRL(queue=queue, loc=locbox, mrk=mrkbox)
    loc = LOC(outbox=queue, inbox=locbox, address=(loc_host, loc_port))
    mrk = MRK(mrk=mrkbox)
    mrk.start()
    loc.start()
    loc.await_running()
    mrk.await_running()
    ctrl.start()
    ctrl.await_running()
    ext.start()
    ext.await_running()


def kill(ext: Tuple[str, int] = ("127.0.0.1", 6667)):
    """kill the localite-flow at the given address

    args
    ----
    ext: Tuple[str, int] = ("127.0.0.1", 6667)
        the host:port where the localite-flow server was setup    

    
    """
    push("cmd", "poison-pill", host=ext[0], port=ext[1])


def start(host: str):
    """start localite-flow in a subprocess
    
    args
    ----
    host: str
        the ip adress of the localite PC

    stop the subprocess gracefully using :meth:`~.kill`

    """
    from localite.flow.ext import available

    p = Popen(["localite-flow", "--host", host], stderr=PIPE, stdout=PIPE)
    print("[", end="")
    while not available():  # pragma no cover
        print(".", end="")
        time.sleep(0.5)
    print("]")
    return p
