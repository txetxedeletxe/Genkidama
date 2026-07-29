from genkidama import start_donor_server, Config

import os
import tomllib

import argparse

import logging

def _build_parser(): # TODO make argument groups
    parser = argparse.ArgumentParser()

    parser.add_argument("bind_address", nargs="?", default="localhost", help="Address to which to bind the server.")

    parser.add_argument("-p","--port", type=int, default=None, help="Port to which to bind the server. If unspecified, the DEFAULT Config value will be used.")

    cert_group = parser.add_mutually_exclusive_group(required=True)
    cert_group.add_argument("--cert_file", default=None, help="CA certificate file with certificates to trust.")
    cert_group.add_argument("--no-auth", dest="no_auth", action="store_true", help="Do not authenticate connections. Use with extreme caution in controlled environments. At your own risk!")

    parser.add_argument("--log-level", type=str, dest="log_level", help="Level at which to do logging. Options are: DEBUG (10), INFO (20), WARNING (30), ERROR (40) or CRITICAL (50); or an integer value between 0 and 100." )

    parser.add_argument("--conf_file", help="File from which to read configuration (in TOML format).")

    parser.set_defaults(no_auth=False)

    return parser


def main():

    parser = _build_parser()
    args = parser.parse_args()

    # TODO do this "if-else" block some other way
    if args.conf_file is not None:
        with open(args.conf_file,"rb") as conf_file:
            conf = tomllib.load(conf_file)

        log_level = None # Set the system default
        if args.log_level is not None:
            log_level = int(args.log_level) if args.log_level.isnumeric() else getattr(logging, args.log_level.upper())
        elif "log_level" in conf:
            log_level = conf["log_level"]
        logging.basicConfig(level=log_level)


        if "server" in conf: # TODO add behaviour for more than one server
            server_conf = conf["server"][0]

            port = None
            if "port" in server_conf:
                port = server_conf["port"]
            elif args.port is not None:
                port = args.port
            address: tuple[str,int] | str = server_conf["bind_address"] if port is None else (server_conf["bind_address"], port)


            if "cert_file" in server_conf:
                cert = server_conf["cert_file"]
            else:
                cert = None if args.no_auth else args.cert_file


    else:
        log_level = None # Set the system default
        if args.log_level is not None:
            log_level = int(args.log_level) if args.log_level.isnumeric() else getattr(logging, args.log_level.upper())
        logging.basicConfig(level=log_level)

        address: tuple[str,int] | str = args.bind_address if args.port is None else (args.bind_address, args.port)
        cert = None if args.no_auth else args.cert_file

    config = Config()
    if cert is not None:
        config.load_donor_ssl_context(cert)

    try:
        start_donor_server(address, CONFIG=config)
    except KeyboardInterrupt:
        logging.info("Shuting down server!")


if __name__ == "__main__":
    main()
