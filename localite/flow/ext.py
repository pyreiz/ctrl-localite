import socket
import threading
import json
from localite.flow import Payload, has_poison
from logging import getLogger

log = getLogger(__name__)
# -----------------------------------------------------------------------------
def read_msg(client: socket.socket) -> Payload:
    "receive byte for byte to read the header telling the message length"
    # parse the message until it is a valid json
    msg = bytearray(b" ")
    while True:
        try:
            prt = client.recv(1)
            msg += prt
            marker, tstamp = json.loads(msg.decode("ascii"))
            log.info(f"Received {marker} for {tstamp}")
            return marker, tstamp
        except json.decoder.JSONDecodeError:
            pass
        except Exception as e:
            log.error(e)
            return Payload(("", None))


class EXT(threading.Thread):
    def __init__(self, queue, host: str = "127.0.0.1", port: int = 6667):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.queue = queue
        self.is_running = threading.Event()

    def run(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, self.port))
        listener.listen(1)  # one  unaccepted client is allowed
        self.is_running.set()
        while self.is_running.is_set():
            try:
                client, address = listener.accept()
                payload = read_msg(client)
                self.queue.put(payload)
                if has_poison(payload):
                    self.is_running.clear()
                    break
            except Exception as e:
                log.error(e)
            finally:
                client.shutdown(socket.SHUT_RDWR)
                client.close()
        log.info("Shutting EXT down")
