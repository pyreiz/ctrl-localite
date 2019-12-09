import os
from pytest import fixture
from localite.flow.loc import LOC, localiteClient, json
from localite.flow.payload import Queue, Payload, put_in_queue, get_from_queue
import time

if "LOCALITE_HOST" in os.environ:
    # on windows: set LOCALITE_HOST=host, e.g.
    # set LOCALITE_HOST=127.0.0.1
    @fixture
    def loc():
        inbox = Queue()
        outbox = Queue()
        loc = LOC(
            host=os.environ["LOCALITE_HOST"], port=6666, inbox=inbox, outbox=outbox
        )
        loc.start()
        loc.await_running()
        yield loc
        pl = Payload("cmd", "poison-pill", 12345)
        put_in_queue(pl, loc.inbox)
        t0 = time.time()
        d = 0
        while loc.is_running.is_set() and d < 7:
            d = time.time() - t0
        assert not loc.is_running.is_set()

    def test_receiving(loc):
        time.sleep(1)
        recv = []
        while loc.outbox.unfinished_tasks:
            pl = get_from_queue(loc.outbox)
            recv.append(pl)
            print(pl)

    def test_setting_amplitude(loc):
        payload = Payload("loc", '{"coil_0_amplitude": 20}', 1)
        put_in_queue(payload, loc.inbox)
        time.sleep(0.1)
        payload = Payload("loc", '{"coil_0_amplitude": 0}', 1)
        put_in_queue(payload, loc.inbox)
        time.sleep(0.1)
        payload = Payload("loc", '{"single_pulse": "coil_0"}', 1)
        put_in_queue(payload, loc.inbox)
