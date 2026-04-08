from genkidama.coms.transport import Transport, SocketTransport, IPTransport, TCPTransport
from genkidama.config import Configurable

import socket
import os

import typing
from typing import Generic, Self

import logging
logger = logging.getLogger(__name__)

TransportT = typing.TypeVar("TransportT", bound=Transport, covariant=True)

class Server(Generic[TransportT]):
    def accept(self) -> TransportT:
        raise NotImplementedError()

class ServerWrapperMixin(Server[TransportT], Generic[TransportT]):

    def __init__(self, wrapped: Server[TransportT] | None = None):
        self._wrapped = self if wrapped is None else typing.cast(Server[TransportT], wrapped)

        # Swap the wrapped recv and send for the wrapping ones
        self.accept, self._accept = self._accept, self._wrapped.accept

    def _accept(self): raise NotImplementedError()

class ForkingServer(ServerWrapperMixin[TransportT], Generic[TransportT]):
    def _accept(self):
        while True: # TODO add a stopping mechanism
            transport = self._accept()

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



