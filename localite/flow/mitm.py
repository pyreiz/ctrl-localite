from localite.flow.ext import EXT
from localite.flow.loc import LOC
from localite.flow.mrk import MRK
from localite.flow.ctrl import CTRL
from localite.flow.payload import Queue

ext_host = "127.0.0.1"
ext_port = 6667
loc_host = "134.2.117.146"
loc_port = 6666

queue = Queue()
locbox = Queue()
mrkbox = Queue()

ext = EXT(host=ext_host, port=ext_port, queue=queue)
ctrl = CTRL(queue=queue, loc=locbox, mrk=mrkbox)
loc = LOC(outbox=queue, inbox=locbox, host=loc_host, port=loc_port)
mrk = MRK(mrk=mrkbox)


mrk.start()
loc.start()
loc.await_running()
mrk.await_running()
ctrl.start()
ctrl.await_running()
ext.start()
ext.await_running()

from localite.flow.payload import Payload
from localite.flow.ext import push

push("mrk", "thisisatest", host=ext_host, port=ext_port)
push("mrk", '{"get:"test"}', host=ext_host, port=ext_port)
push("loc", '{"get":"current_instrument"}', host=ext_host, port=ext_port)
