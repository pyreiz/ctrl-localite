from localite.flow.mitm import start_threaded
from localite.flow.mitm import kill as kill_flow
from localite.flow.mock import Mock
from localite.flow.mock import kill as kill_mock
import argparse


def flow():
    parser = argparse.ArgumentParser("localite-flow")
    parser.add_argument(
        "--host", type=str, help="The IP-Adress of the localite-PC", default="",
    )
    parser.add_argument("--kill", action="store_true")
    args, unknown = parser.parse_known_args()
    if args.kill:
        kill_flow(("127.0.0.1", 6667))
    else:
        if args.host == "":
            parser.print_help()
        else:
            start_threaded(loc_host=args.host, ext=("127.0.0.1", 6667))


def mock():
    parser = argparse.ArgumentParser("localite-flow")
    parser.add_argument("--kill", action="store_true")
    args, unknown = parser.parse_known_args()
    if args.kill:
        kill_mock()
    else:
        mock = Mock()
        mock.start()
        mock.await_running()

