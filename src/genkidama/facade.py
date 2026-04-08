from genkidama.coms import endpoint
from genkidama.core.genkidama_session import RemoteGenkidamaSession
from genkidama.core.donor_session import RemoteDonorSession, LocalDonorSession

from genkidama.coms.endpoint import TerminalEndpoint
from genkidama.coms.codec import BinaryCodec
from genkidama.coms.transport import TCPTransport
from genkidama.coms.server import TCPSocketServer, ForkingServer

from genkidama import DEFAULTS

import typing
import logging
logger = logging.getLogger(__name__)

# TODO add more options
# TODO add config parameter
def connect_to_session(address: tuple[str,int] | str) -> RemoteGenkidamaSession:
    address = typing.cast(tuple[str, int], address) if isinstance(address, tuple) else (address, DEFAULTS.SERVER_PORT)
    transport = TCPTransport.connect(address)
    codec = BinaryCodec()

    logger.info(f"Connected to donor {address}")

    endpoint = TerminalEndpoint(codec, transport)
    donor_session = endpoint.mirror_endpoint = RemoteDonorSession(endpoint)

    endpoint.start()

    return donor_session.master_session

def start_server(port: int | None = None):
    port = DEFAULTS.SERVER_PORT if port is None else port

    server = ForkingServer(TCPSocketServer(("localhost",port)))
    tcp_transport = server.accept()

    endpoint = TerminalEndpoint(BinaryCodec(), tcp_transport)
    donor_session = endpoint.mirror_endpoint = LocalDonorSession(endpoint)

    donor_session.start()
    endpoint.start()
    endpoint.join()

    logger.info(f"Connection terminated")
