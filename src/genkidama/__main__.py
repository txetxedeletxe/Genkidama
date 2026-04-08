from genkidama import start_server

import argparse

import logging

def _build_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument("bind_address", help="Address to which to bind the server.")
    parser.add_argument("-p","--port", type=int, default=None, dest="bind_port", help="Port to which to bind the server. If unspecified, the DEFAULT Config value will be used.")

    return parser


def run_server():
    logging.basicConfig(level=logging.DEBUG)

    parser = _build_parser()
    args = parser.parse_args()

    address: tuple[str,int] | str = args.bind_address if args.bind_port is None else (args.bind_address, args.bind_port)
    start_server(address)


if __name__ == "__main__":
    run_server()
