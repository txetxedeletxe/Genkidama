from genkidama.model import Validable

import socket

from typing import Self

class SocketContainer(Validable):
    ADRESS_FAMILY: socket.AddressFamily | None = None
    SOCKET_KIND: socket.SocketKind | None = None

    @classmethod
    def _create_socket(cls: type[Self]) -> socket.socket:
        if cls.ADRESS_FAMILY is None or cls.SOCKET_KIND is None:
            raise ValueError(f"Type {cls} does not fully specify the family/kind of socket to instantiate. Use 'create_socket' with a Final subclass of SocketContainer.")

        return socket.socket(cls.ADRESS_FAMILY, cls.SOCKET_KIND)

    def __init__(self, socket: socket.socket) -> None:
        self.socket = socket

        self.validate()
        self.ADRESS_FAMILY, self.SOCKET_KIND = socket.family, socket.type

    def validate(self):
        # TODO use custom exceptions
        if self.ADRESS_FAMILY is not None:
            assert self.ADRESS_FAMILY == self.socket.family

        if self.SOCKET_KIND is not None:
            assert self.SOCKET_KIND == self.socket.type

class StreamSocketContainer(SocketContainer):
    SOCKET_KIND = socket.SOCK_STREAM

class IPSocketContainer(SocketContainer):
    ADRESS_FAMILY = socket.AF_INET # TODO add support for IPv6 (decide address family dynamically)

class TCPSocketContainer(StreamSocketContainer, IPSocketContainer): pass

class SSLSocketContainer(StreamSocketContainer): pass
