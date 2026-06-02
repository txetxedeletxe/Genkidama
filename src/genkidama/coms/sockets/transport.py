from .container import SocketContainer, IPSocketContainer, TCPSocketContainer, SSLSocketContainer

from genkidama.config import Config, Configurable
from genkidama.coms.transport import Transport, TransportWrapperMixin, BinaryStreamTransport

from genkidama.configheader import ConfigHeader, SocketConfigHeader

import socket
import ssl

import typing
from typing import Self

class SocketTransport(Transport[bytes], SocketContainer, Configurable):

    @classmethod
    def connect(cls: type[Self], address: tuple[str, int] | str, *, CONFIG: Config | None = None) -> Self:
        sck = cls._create_socket()
        sck.connect(address)

        transport = cls(sck, CONFIG=CONFIG)
        transport.handshake()

        return transport

    def __init__(self, socket: socket.socket, *, CONFIG: Config | None = None):
        Configurable.__init__(self, CONFIG=CONFIG)
        SocketContainer.__init__(self, socket)

    # API
    def send(self, payload: bytes):
        self.socket.sendall(payload)

    def recv(self) -> bytes:
        return self.socket.recv(self.CONFIG.SOCKET_BUFFERSIZE)

    # TODO handle edge cases where handshake is used in the middle of the operation (disallow this)
    def handshake(self):
        header = SocketConfigHeader.from_config(self.CONFIG)

        self.send(header.encode())
        other_header = header.decode(self.recv())

        header.assert_compatible(other_header)

class IPTransport(SocketTransport, IPSocketContainer): pass # IPv4 transport

class TCPTransport(IPTransport, BinaryStreamTransport, TCPSocketContainer):
    def __init__(self, socket: socket.socket, *, CONFIG: Config | None = None):
        BinaryStreamTransport.__init__(self, CONFIG=CONFIG)
        IPTransport.__init__(self, socket, CONFIG=CONFIG)

class SSLTransport(SocketTransport, TransportWrapperMixin[bytes], SSLSocketContainer):

    def __init__(self, wrapped: SocketTransport | None = None, *, CONFIG: Config | None = None):
        #TransportWrapperMixin.__init__(self)
        self.__wrapped, _ = SSLTransport.wrap(self, wrapped)
        self.__wrapped = typing.cast(SocketTransport, self.__wrapped)

        SocketTransport.__init__(self, self.__wrapped.socket, CONFIG=CONFIG)

        # TODO improve this
        if self.CONFIG.SSL_CONTEXT is None:
            raise ValueError("SSL Context is not initialized. Cannot create a SSL Socket.")
        server_side = self.CONFIG.SSL_CONTEXT.verify_mode != ssl.CERT_REQUIRED
        self.socket = self.CONFIG.SSL_CONTEXT.wrap_socket(self.socket, server_side=server_side)


# TODO write other transport methods (e.g. UDPTransport)
