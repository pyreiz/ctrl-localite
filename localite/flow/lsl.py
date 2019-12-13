import os

if not os.environ.get("READTHEDOCS", False):
    from pylsl import StreamInfo, StreamInlet, StreamOutlet, local_clock, resolve_stream
else:  # pragma no cover
    from time import time as local_clock

    def resolve_stream(*args, **kwargs):
        pass

    StreamInfo = StreamInlet = StreamOutlet = resolve_stream
