from .container import SocketContainer, IPSocketContainer, TCPSocketContainer, SSLSocketContainer
from .transport import SocketTransport, IPTransport, TCPTransport, SSLTransport

from genkidama.config import Config, Configurable
from genkidama.coms.server import Server, ServerWrapperMixin, ForkingServer

import ssl
import os

import typing
from typing import TypeVar, Generic

import logging
logger = logging.getLogger(__name__)


SocketTransportT = TypeVar("SocketTransportT", bound=SocketTransport, covariant=True)
class SocketServer(SocketContainer, Server[SocketTransportT], Configurable, Generic[SocketTransportT]):
    _TRANSPORT_FACTORY: type[SocketTransportT] # TODO this is not necessarily a class, it can be a callable that returns the type # TODO change this to a constructor parameter

    def __init__(self, address: tuple[str, int] | str, *, CONFIG: Config | None = None):

        socket_ = self._create_socket()
        socket_.bind(address)
        socket_.listen() # TODO put a listen limit in Config?

        Configurable.__init__(self, CONFIG=CONFIG)
        SocketContainer.__init__(self, socket_)

    def accept(self, *, handshake=True) -> SocketTransportT:
        sock, addr = self.socket.accept()

        logger.info(f"Connection established: {addr}")

        transport = self._TRANSPORT_FACTORY(sock, CONFIG=self.CONFIG)
        if handshake: transport.handshake()
        return transport


class ForkingSocketServer(SocketServer[SocketTransportT], ForkingServer[SocketTransportT], Generic[SocketTransportT]):
    def __init__(self, wrapped: SocketServer[SocketTransportT] | None = None):
        self.__wrapped, _ = ForkingSocketServer[SocketTransportT].wrap(self, wrapped)
        self.__wrapped = typing.cast(SocketServer[SocketTransportT], self.__wrapped)

        ForkingServer.__init__(self, self.__wrapped)
        SocketContainer.__init__(self, self.__wrapped.socket)


IPTransportT = TypeVar("IPTransportT", bound=IPTransport, covariant=True)
class IPSocketServer(IPSocketContainer, SocketServer[IPTransportT], Generic[IPTransportT]): pass # IPv4 socket server

class TCPSocketServer(TCPSocketContainer, IPSocketServer[TCPTransport]):
    _TRANSPORT_FACTORY = TCPTransport

class SSLSocketServer(SSLSocketContainer, SocketServer[SSLTransport], ServerWrapperMixin[SocketServer[SocketTransportT], SSLTransport], Generic[SocketTransportT]):

    @staticmethod
    def _update_PRNG():
        try:
            ssl.RAND_bytes(32)
        except:
            logger.error("Could not update PRNG state of the SSL server! This could result in a security issue!")

    def __init__(self, wrapped: SocketServer[SocketTransportT] | None = None, *, CONFIG: Config | None = None):
        self.__wrapped, (self.__accept, *_) = SSLSocketServer[SocketTransportT].wrap(self,wrapped)

        # Initialize socket
        SSLSocketContainer.__init__(self, self.__wrapped.socket)
        Configurable.__init__(self, CONFIG=CONFIG)

        # Do this to ensure SSL PRNG is updated when forking # TODO put this somewhere else
        os.register_at_fork(after_in_parent=self._update_PRNG)


    def accept(self, *, handshake=True) -> SSLTransport:
        transport = self.__accept(handshake=handshake) # Handshake happens before!
        return SSLTransport(transport, CONFIG=self.CONFIG)
