from genkidama.coms.transport import Transport, SocketTransport, IPTransport, TCPTransport, SSLTransport
from genkidama.coms.socketcontainer import SocketContainer, IPSocketContainer, TCPSocketContainer, SSLSocketContainer
from genkidama.config import Config, Configurable

import ssl
import socket
import os

import types
import typing
from typing import Protocol, Callable, Generic, Self

import logging
logger = logging.getLogger(__name__)

TransportT = typing.TypeVar("TransportT", bound=Transport, covariant=True)

class Server(Protocol, Generic[TransportT]):
    def accept(self, *, handshake=True) -> TransportT: raise NotImplementedError()


ServerT = typing.TypeVar("ServerT", bound=Server, covariant=True)
class ServerWrapperMixin(Server[TransportT], Generic[ServerT, TransportT]):

    @classmethod
    def wrap(cls: type[Self], self: Self, wrapped: ServerT | None = None):
        wrapped_ = self if wrapped is None else wrapped

        self.accept, accept_return = types.MethodType(cls.accept, self), wrapped_.accept

        return wrapped_, accept_return

    def __init__(self) -> None:
        self.__wrapped, self.__accept = ServerWrapperMixin.wrap(self)

    def accept(self, *, handshake=True) -> TransportT:
        return self.__accept(handshake=handshake)



class ForkingServer(ServerWrapperMixin[Server[TransportT], TransportT], Generic[TransportT]):
    def __init__(self, wrapped: Server[TransportT] | None = None):
        ServerWrapperMixin.__init__(self)
        self.__wrapped, self.__accept = ForkingServer[TransportT].wrap(self, wrapped)

    def accept(self, *, handshake=True):
        while True: # TODO add a stopping mechanism # TODO Add max connections
            transport = self.__accept(handshake=False)

            if os.fork() == 0: # child
                if handshake: transport.handshake()
                return transport

            # TODO close transport in parent

# Socket Servers
SocketTransportT = typing.TypeVar("SocketTransportT", bound=SocketTransport, covariant=True)
class SocketServer(Server[SocketTransportT], SocketContainer, Configurable, Generic[SocketTransportT]):
    _TRANSPORT_FACTORY: type[SocketTransportT] # TODO this is not necessarily a class, it can be a callable that returns the type

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
        self.__wrapped, self.__accept = ForkingSocketServer[SocketTransportT].wrap(self, wrapped)
        self.__wrapped = typing.cast(SocketServer[SocketTransportT], self.__wrapped)

        # TODO improve this
        ForkingServer.__init__(self)
        SocketContainer.__init__(self, self.__wrapped.socket)

    def accept(self, *, handshake=True) -> SocketTransportT:
        return self.__accept(handshake=handshake)



IPTransportT = typing.TypeVar("IPTransportT", bound=IPTransport, covariant=True)
class IPSocketServer(SocketServer[IPTransportT], IPSocketContainer, Generic[IPTransportT]): pass # IPv4 socket server

class TCPSocketServer(IPSocketServer[TCPTransport], TCPSocketContainer):
    _TRANSPORT_FACTORY = TCPTransport

class SSLSocketServer(SocketServer[SSLTransport], ServerWrapperMixin[SocketServer[SocketTransportT], SSLTransport], SSLSocketContainer, Generic[SocketTransportT]):

    @staticmethod
    def _update_PRNG():
        try:
            ssl.RAND_bytes(32)
        except:
            logger.error("Could not update PRNG state of the SSL server! This could result in a security issue!")

    def __init__(self, wrapped: SocketServer[SocketTransportT] | None = None, *, CONFIG: Config | None = None):
        self.__wrapped, self.__accept = SSLSocketServer[SocketTransportT].wrap(self,wrapped)

        # Initialize socket # TODO improve this
        SSLSocketContainer.__init__(self, self.__wrapped.socket)
        Configurable.__init__(self, CONFIG=CONFIG)

        # Do this to ensure SSL PRNG is updated when forking # TODO put this somewhere else
        os.register_at_fork(after_in_parent=self._update_PRNG)


    def accept(self, *, handshake=True) -> SSLTransport:
        transport = self.__accept(handshake=handshake) # Handshake happens before!
        return SSLTransport(transport, CONFIG=self.CONFIG)



