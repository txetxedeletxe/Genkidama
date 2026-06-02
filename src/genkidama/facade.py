from genkidama.config import Config, DEFAULTS
from genkidama.configheader import IncompatibleHeaderException
from genkidama.core.genkidamasession import RemoteGenkidamaSession
from genkidama.core.donorsession import RemoteDonorSession, LocalDonorSession

from genkidama.coms import BinaryCodec, TCPTransport, SSLTransport, TCPSocketServer, ForkingSocketServer, SSLSocketServer, TerminalEndpoint

import typing
import logging
logger = logging.getLogger(__name__)

# TODO rethink this

# TODO add more options
def connect_to_session(address: tuple[str,int] | str, *, CONFIG: Config | None = None) -> RemoteGenkidamaSession:
    DEFAULTS_ = DEFAULTS if CONFIG is None else CONFIG
    address = typing.cast(tuple[str, int], address) if isinstance(address, tuple) else (address, DEFAULTS_.SERVER_PORT)

    codec = BinaryCodec(CONFIG=CONFIG)

    transport = TCPTransport.connect(address, CONFIG=CONFIG)
    if DEFAULTS_.SSL_CONTEXT is not None:
        transport = SSLTransport(transport, CONFIG=CONFIG)

    logger.info(f"Connected to donor {address}")

    endpoint = TerminalEndpoint(codec, transport, CONFIG=CONFIG)
    donor_session = endpoint.mirror_endpoint = RemoteDonorSession(endpoint, CONFIG=CONFIG)

    endpoint.start()

    return donor_session.master_session

def start_donor_server(address: tuple[str,int] | str, *, CONFIG: Config | None = None):
    DEFAULTS_ = DEFAULTS if CONFIG is None else CONFIG
    address = typing.cast(tuple[str, int], address) if isinstance(address, tuple) else (address, DEFAULTS_.SERVER_PORT)

    server = ForkingSocketServer(TCPSocketServer(address, CONFIG=CONFIG))

    if DEFAULTS_.SSL_CONTEXT is not None:
        server = SSLSocketServer(server, CONFIG=CONFIG) # SSL wrapper outside of forking so that it can happen in another process
    else:
        logger.warning("Running Donor Server without authentication! This should only be done with extereme caution and with the server is listening in a very hermetic network (like localhost).")

    codec = BinaryCodec(CONFIG=CONFIG)

    # TODO Clean this up. Separate server and donor isntaces better.
    try:
        transport = server.accept()
    except KeyboardInterrupt as e:
        server.close() # TODO Change this for a with statement
        raise e
    except OSError as e:
        logger.error("Could not stablish a secure connection with an incomming connection:\n\n{}\n\nDropping connection.".format(e))
        exit(-1)
    except IncompatibleHeaderException as e:
        logger.error("Exchanged Headers are not compatible:\n\n{}\n\nDropping connection.".format(e))
        exit(-1)

    endpoint = TerminalEndpoint(codec, transport)
    donor_session = endpoint.mirror_endpoint = LocalDonorSession(endpoint, CONFIG=CONFIG)

    donor_session.start()
    endpoint.start()

    try:
        endpoint.join()
        logger.info(f"Connection terminated")
    except KeyboardInterrupt:
        logger.warning(f"KeyboardInterrupt. Shutting down connection.")

    exit(-1)

