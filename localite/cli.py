from localite.flow.mitm import start_threaded, kill

import argparse


def flow():
    parser = argparse.ArgumentParser("localite-flow")
    parser.add_argument(
        "--host", type=str, help="The IP-Adress of the localite-PC", default="",
    )
    parser.add_argument("--kill", action="store_true")
    args, unknown = parser.parse_known_args()
    if args.kill:
        kill(("127.0.0.1", 6667))
    else:
        if args.host == "":
            parser.print_help()
        else:
            start_threaded(loc_host=args.host, ext=("127.0.0.1", 6667))
