import functools
from ssl import SSLContext, SSLSocket
from genkidama.config import Configurable

import socket
import threading

import typing
from typing import Any, Callable, Generic, Self, override

import logging
logger = logging.getLogger(__name__)

try:
    import ssl
except ModuleNotFoundError:
    logger.warning("ssl module not found, cannot use secure sockets. Install the ssl module to enable authenticated/encrypted connections.")

MediaT = typing.TypeVar("MediaT")
class Transport(Generic[MediaT]):
    def send(self, payload: MediaT): raise NotImplementedError()
    def recv(self) -> MediaT: raise NotImplementedError()
    # TODO implement close

class TransportWrapperMixin(Transport[MediaT], Generic[MediaT]):

    @classmethod
    def wrap(cls: type[Self], self: Self, wrapped: Transport[MediaT] | None = None):
        wrapped_ = self if wrapped is None else wrapped

        self.send, send_return = functools.partial(cls.send,self), wrapped_.send
        self.recv, recv_return = functools.partial(cls.recv,self), wrapped_.recv

        return wrapped_, (send_return, recv_return)

class BinaryStreamTransport(TransportWrapperMixin[bytes], Configurable):
    def __init__(self, wrapped: Transport[bytes] | None = None):
        self.__wrapped, (self.__send, self.__recv) = BinaryStreamTransport.wrap(self, wrapped)

        self._recv_buffer = bytearray()
        self._lock = threading.RLock()

    def send(self, payload: bytes):
        payload_length = len(payload)
        framed_payload = payload_length.to_bytes(self.CONFIG.PAYLOAD_FRAME_LENGTH) + payload

        self.__send(framed_payload)


    def recv(self) -> bytes:
        with self._lock:
            while len(self._recv_buffer) < self.CONFIG.PAYLOAD_FRAME_LENGTH:

                recv_payload = self.__recv()
                if not recv_payload: # Connection closed
                    raise ConnectionResetError("Connection closed by peer.")

                self._recv_buffer += recv_payload

            expecting_bytes = int.from_bytes(self._recv_buffer[:self.CONFIG.PAYLOAD_FRAME_LENGTH])
            expecting_bytes += self.CONFIG.PAYLOAD_FRAME_LENGTH

            while len(self._recv_buffer) < expecting_bytes:
                recv_payload = self.__recv()
                self._recv_buffer += recv_payload

            recved = bytes(self._recv_buffer[self.CONFIG.PAYLOAD_FRAME_LENGTH:expecting_bytes])
            del self._recv_buffer[:expecting_bytes]

            return recved

class SocketTransport(Transport[bytes], Configurable):

    ADRESS_FAMILY: socket.AddressFamily
    SOCKET_KIND: socket.SocketKind

    @classmethod
    def connect(cls: type[Self], address: tuple[str, int] | str) -> Self:
        sck = socket.socket(cls.ADRESS_FAMILY, cls.SOCKET_KIND)
        sck.connect(address)

        return cls(sck)

    def __init__(self, socket: socket.socket):
        self.socket = socket
        # TODO validate socket type

    # API
    def send(self, payload: bytes):
        self.socket.sendall(payload)

    def recv(self) -> bytes:
        return self.socket.recv(self.CONFIG.SOCKET_BUFFERSIZE)


class IPTransport(SocketTransport): # IPv4 transport
    ADRESS_FAMILY = socket.AF_INET

class TCPTransport(IPTransport, BinaryStreamTransport):
    SOCKET_KIND = socket.SOCK_STREAM

    def __init__(self, socket: socket.socket):
        IPTransport.__init__(self, socket)
        BinaryStreamTransport.__init__(self)

class SSLTransport(SocketTransport, TransportWrapperMixin[bytes]):

    def __init__(self, wrapped: SocketTransport | None = None, authenticator: bool = False):
        if self.CONFIG.SSL_CONTEXT is None: # TODO improve this check
            raise ValueError("CONFIG.SSL_CONTEXT is None, configure the SSL context before using SSLTransport.")

        self.__wrapped, _ = SSLTransport.wrap(self, wrapped)
        self.__wrapped = typing.cast(SocketTransport, self.__wrapped)

        self.ADRESS_FAMILY = self.__wrapped.ADRESS_FAMILY
        self.SOCKET_KIND = self.__wrapped.SOCKET_KIND

        SocketTransport.__init__(self, self.__wrapped.socket)
        self.socket: ssl.SSLSocket = self.CONFIG.SSL_CONTEXT.wrap_socket(self.socket, server_side=not authenticator)


# TODO write other transport methods (e.g. UDPTransport)




