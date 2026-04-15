from genkidama.coms import endpoint
from genkidama.core.genkidama_session import RemoteGenkidamaSession
from genkidama.core.donor_session import RemoteDonorSession, LocalDonorSession

from genkidama.coms.endpoint import TerminalEndpoint
from genkidama.coms.codec import BinaryCodec
from genkidama.coms.transport import TCPTransport, SSLTransport
from genkidama.coms.server import TCPSocketServer, ForkingServer, SSLForkingServer

from genkidama import DEFAULTS

import typing
import logging
logger = logging.getLogger(__name__)

# TODO add more options
# TODO add config parameter
def connect_to_session(address: tuple[str,int] | str, *, authenticate: bool = False) -> RemoteGenkidamaSession:
    address = typing.cast(tuple[str, int], address) if isinstance(address, tuple) else (address, DEFAULTS.SERVER_PORT)

    if authenticate:
        transport = SSLTransport(TCPTransport.connect(address))
    else:
        transport = TCPTransport.connect(address)

    codec = BinaryCodec()
    logger.info(f"Connected to donor {address}")

    endpoint = TerminalEndpoint(codec, transport)
    donor_session = endpoint.mirror_endpoint = RemoteDonorSession(endpoint)

    endpoint.start()

    return donor_session.master_session

def start_donor_server(address: tuple[str,int] | str, cainfo: tuple[str|None,str|None] | None):
    address = typing.cast(tuple[str, int], address) if isinstance(address, tuple) else (address, DEFAULTS.SERVER_PORT)

    if cainfo is None:
        logger.warning("Running Donor Server without authentication! This should only be done with extereme caution and with the server is listening in a very hermetic network (like localhost).")
        server = ForkingServer(TCPSocketServer(address))
    else:
        DEFAULTS.load_donor_ssl_context(*cainfo)

    server = SSLForkingServer(TCPSocketServer(address)) # SSL wrapper outside of forking so that it can happen in another process

    try:
        tcp_transport = server.accept()
    except OSError as e:
            logger.critical("Could not stablish a secure connection with an incomming connection. Dropping connection.")
            exit(-1)

    endpoint = TerminalEndpoint(BinaryCodec(), tcp_transport)
    donor_session = endpoint.mirror_endpoint = LocalDonorSession(endpoint)

    donor_session.start()
    endpoint.start()
    endpoint.join()

    logger.info(f"Connection terminated")
