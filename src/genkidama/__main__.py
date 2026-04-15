from genkidama import start_donor_server

import argparse

import logging

def _build_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument("bind_address", help="Address to which to bind the server.")
    parser.add_argument("-p","--port", dest="bind_port", type=int, default=None, help="Port to which to bind the server. If unspecified, the DEFAULT Config value will be used.")

    cert_group = parser.add_mutually_exclusive_group(required=True)
    cert_group.add_argument("--cafile", default=None, help="CA certificates file with the certificates to trust.")
    cert_group.add_argument("--capath", default=None, help="Path of directory with CA certificate files with the certificates to trust.")
    cert_group.add_argument("--no-auth", dest="no_auth", action="store_true", help="Do not authenticate connections. Use with extreme caution in controlled environments. At your own risk!")

    parser.add_argument("--log-level", default="INFO", type=str, dest="log", help="Level at which to do logging. Options are: DEBUG (10), INFO (20), WARNING (30), ERROR (40) or CRITICAL (50); or an integer value between 0 and 100." )

    parser.set_defaults(no_auth=False)

    return parser


def run_server():

    parser = _build_parser()
    args = parser.parse_args()

    log_level = int(args.log) if args.log.isnumeric() else getattr(logging, args.log.upper())
    logging.basicConfig(level=log_level)


    address: tuple[str,int] | str = args.bind_address if args.bind_port is None else (args.bind_address, args.bind_port)
    cainfo = (args.cafile, args.capath) if not args.no_auth else None
    start_donor_server(address, cainfo)


if __name__ == "__main__":
    run_server()
