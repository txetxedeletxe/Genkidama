import functools
from genkidama.coms.transport import Transport, SocketTransport, IPTransport, TCPTransport, SSLTransport
from genkidama.config import Configurable

import socket
import os

import typing
from typing import Callable, Generic, Self

import logging
logger = logging.getLogger(__name__)

try:
    import ssl
except ModuleNotFoundError:
    logger.warning("ssl module not found, cannot use secure sockets. Install the ssl module to enable authenticated connections.")

TransportTOut = typing.TypeVar("TransportTOut", bound=Transport, covariant=True)
TransportTIn = typing.TypeVar("TransportTIn", bound=Transport, covariant=True)

class Server(Generic[TransportTOut]):
    def accept(self) -> TransportTOut:
        raise NotImplementedError()

class ServerWrapperMixin(Server[TransportTOut], Generic[TransportTIn, TransportTOut]):

    @classmethod
    def wrap(cls: type[Self], self: Self, wrapped: Server[TransportTIn] | None = None):
        wrapped_ = self if wrapped is None else wrapped
        self.accept, accept_return = functools.partial(cls.accept, self), wrapped_.accept

        return wrapped_, accept_return


class ForkingServer(ServerWrapperMixin[TransportTOut, TransportTOut], Generic[TransportTOut]):
    def __init__(self, wrapped: Server[TransportTOut] | None = None):
        self.__wrapped, self.__accept = ForkingServer.wrap(self, wrapped)

    def accept(self):
        while True: # TODO add a stopping mechanism
            transport = self.__accept()

            if os.fork() == 0: # child
                return transport

# Socket Servers
SocketTransportT = typing.TypeVar("SocketTransportT", bound=SocketTransport, covariant=True)
class SocketServer(Server[SocketTransportT], Configurable, Generic[SocketTransportT]):

    # TODO Unify these fields with those in Transport using new Base Classes
    ADRESS_FAMILY: socket.AddressFamily
    SOCKET_KIND: socket.SocketKind

    _TRANSPORT_FACTORY: type[SocketTransportT]

    def __init__(self, address: tuple[str, int] | str):

        self.socket = socket.socket(self.ADRESS_FAMILY, self.SOCKET_KIND)
        self.socket.bind(address)
        self.socket.listen() # TODO put a listen limit in Config?

    def accept(self) -> SocketTransportT:
        sock, addr = self.socket.accept()

        logger.info(f"Connection established: {addr}")

        return self._TRANSPORT_FACTORY(sock)

IPTransportT = typing.TypeVar("IPTransportT", bound=IPTransport, covariant=True)
class IPSocketServer(SocketServer[IPTransportT], Generic[IPTransportT]): # IPv4 socket server
    ADRESS_FAMILY = socket.AF_INET

class TCPSocketServer(IPSocketServer[TCPTransport]):
    SOCKET_KIND = socket.SOCK_STREAM

    _TRANSPORT_FACTORY = TCPTransport

class SSLSocketServer(SocketServer[SSLTransport], ServerWrapperMixin[SocketTransportT, SSLTransport], Generic[SocketTransportT]):
    def __init__(self, wrapped: Server[SocketTransportT] | None = None):
        self.__wrapped, self.__accept = SSLSocketServer[SocketTransportT].wrap(self,wrapped)

    def accept(self) -> SSLTransport:
        transport = self.__accept()
        return SSLTransport(transport, authenticator=True)

class SSLForkingServer(SSLSocketServer[SocketTransportT], ServerWrapperMixin[SocketTransportT, SSLTransport], Generic[SocketTransportT]):
    def __init__(self, wrapped: Server[SocketTransportT] | None = None):
        self.__wrapped, self.__accept = SSLForkingServer[SocketTransportT].wrap(self,wrapped)

    def accept(self) -> SSLTransport:
        while True: # TODO add a stopping mechanism
            transport = self.__accept()

            if os.fork() == 0: # child
                return SSLTransport(transport, authenticator=True)
            else:
                import ssl
                ssl.RAND_bytes(1024) # Do this to update parent SSL PRNG


