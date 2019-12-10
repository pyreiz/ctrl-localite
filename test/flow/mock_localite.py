import socket
import json
import pylsl
import threading
import time
from typing import List
from pylsl import local_clock
from localite.flow.payload import Queue, get_from_queue, put_in_queue, Payload
from localite.flow.loc import localiteClient, ignored_localite_messages


class Mock(threading.Thread):
    def __init__(self, host: str = "127.0.0.1", port: int = 6666):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.is_running = threading.Event()

    def await_running(self):
        while not self.is_running.is_set():  # pragma no cover
            pass

    @staticmethod
    def read_msg(client: socket.socket) -> dict:
        "parse the message"
        t0 = time.time()
        client.settimeout(0.1)
        msg = b" "
        while True:
            try:
                prt = client.recv(1)
                msg += prt
                msg = json.loads(msg.decode("ascii"))
                return msg
            except json.JSONDecodeError as e:  # pragma no cover
                pass
            except socket.timeout:
                return None
            except Exception as e:  # pragma no cover
                print("MOCK:READ_MSG:", e)
                return None
        return None

    @staticmethod
    def append(outqueue: List[dict], is_running: threading.Event):
        cnt = 0
        from queue import Full

        modulo = len(ignored_localite_messages)
        while is_running.is_set():
            time.sleep(1)

            cnt += 1
            if cnt > modulo + 1:
                cnt = 0
            elif cnt > modulo:
                msg = {"coil_0_position": "None"}
            else:
                msg = ignored_localite_messages[cnt]
            try:
                outqueue.put_nowait(msg)
            except Full:
                outqueue.get()
                outqueue.task_done()
                outqueue.put(msg)
            print("MOCK:APP", outqueue.unfinished_tasks)

    def run(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, self.port))
        listener.settimeout(1)
        listener.listen(1)  # one  unaccepted client is allowed
        outqueue = Queue(maxsize=10)
        outqueue.put({"coil_0_position": "None"})
        self.is_running.set()
        appender = threading.Thread(
            target=self.append, args=(outqueue, self.is_running,)
        )
        appender.start()
        print("Starting MOCK")
        while self.is_running.is_set():
            try:
                client = None
                client, address = listener.accept()
                print("MOCK:CLIENT", address)
                msg = self.read_msg(client)
                if msg is not None:
                    print("MOCK:RECV", msg)
                    if "cmd" in msg.keys() and "poison-pill" in msg.values():
                        self.is_running.clear()
                        break
                    if "get" in msg.keys():
                        key = msg["get"]
                        # this client is not the localiteClient! but a simple socket
                        outqueue.put({key: "answer"})

                # always send a message, if there is none queued, wait
                # until one is available
                while outqueue.unfinished_tasks == 0:
                    time.sleep(0.01)
                if client is not None:
                    item = outqueue.get_nowait()
                    outqueue.task_done()
                    print("MRK:REM", item, outqueue.unfinished_tasks)
                    msg = json.dumps(item).encode("ascii")
                    client.sendall(msg)
                    client.close()
            except socket.timeout:
                client = None
            except (
                ConnectionError,
                ConnectionAbortedError,
                ConnectionResetError,
                ConnectionRefusedError,
            ):
                client = None
            except Exception as e:  # pragma no cover
                print("MOCK:RUN", str(e))

            time.sleep(0.001)
        print("Shutting MOCK down")

    def kill(self):
        client = localiteClient(self.host, self.port)
        msg = {"cmd": "poison-pill"}
        msg = json.dumps(msg)
        client.send(msg)


# if __name__ == "__main__":
#     host = "127.0.0.1"
#     port = 6666
#     mock = Mock(host=host, port=port)
#     mock.start()
#     mock.await_running()
# client = localiteClient("134.2.117.146", port)

# inbox = Queue()
# outbox = Queue()
# loc = LOC(host=host, port=port, inbox=inbox, outbox=outbox)
# loc.start()
# loc.await_running()

# def listen(host, port):

#     while True:
#         try:
#             item = get_from_queue(loc.outbox)
#             if item is None:
#                 time.sleep(0.001)
#             else:
#                 print(item)
#         except Exception as e:
#             print(e)

# t = threading.Thread(target=listen, args=(host, port,))
# t.start()
