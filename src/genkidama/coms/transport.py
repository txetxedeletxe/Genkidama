from genkidama.config import Config, Configurable
from genkidama.configheader import ConfigHeader, SocketConfigHeader
from genkidama.coms.socketcontainer import SocketContainer, IPSocketContainer, TCPSocketContainer, SSLSocketContainer

import ssl
import socket
import threading

import types
import typing
from typing import Protocol, Any, Callable, Generic, Self, override

import logging
logger = logging.getLogger(__name__)

MediaT = typing.TypeVar("MediaT")
class Transport(Protocol, Generic[MediaT]):
    def send(self, payload: MediaT): raise NotImplementedError()
    def recv(self) -> MediaT: raise NotImplementedError()

    def handshake(self): raise NotImplementedError
    # TODO implement close


class TransportWrapperMixin(Transport[MediaT], Generic[MediaT]):

    @classmethod
    def wrap(cls: type[Self], self: Self, wrapped: Transport[MediaT] | None = None):
        wrapped_ = self if wrapped is None else wrapped

        self.send, send_return = types.MethodType(cls.send,self), wrapped_.send
        self.recv, recv_return = types.MethodType(cls.recv,self), wrapped_.recv
        self.handshake, handshake_return = types.MethodType(cls.handshake,self), wrapped_.handshake

        return wrapped_, (send_return, recv_return, handshake_return)

    def __init__(self, wrapped: Transport[MediaT] | None = None):
        self.__wrapped, (self.__send, self.__recv, self.__handshake) = TransportWrapperMixin.wrap(self, wrapped)

    def send(self, payload: MediaT): return self.__send(payload)
    def recv(self) -> MediaT: return self.__recv()
    def handshake(self): return self.__handshake()


class BinaryStreamTransport(TransportWrapperMixin[bytes], Configurable):
    def __init__(self, wrapped: Transport[bytes] | None = None, *, CONFIG: Config | None = None):
        TransportWrapperMixin.__init__(self)
        self.__wrapped, (self.__send, self.__recv, _) = BinaryStreamTransport.wrap(self, wrapped)

        self.__recv_buffer = bytearray() # TODO Change this for a circular buffer
        self.__lock = threading.RLock()

        Configurable.__init__(self, CONFIG=CONFIG)

    # TODO find a way to use weak references instead of copying the buffers
    def send(self, payload: bytes):
        payload_length = len(payload)
        framed_payload = payload_length.to_bytes(self.CONFIG.PAYLOAD_FRAME_LENGTH) + payload

        self.__send(framed_payload)

    def recv(self) -> bytes:
        with self.__lock:
            while len(self.__recv_buffer) < self.CONFIG.PAYLOAD_FRAME_LENGTH:

                recv_payload = self.__recv()
                if not recv_payload: # Connection closed
                    raise ConnectionResetError("Connection closed by peer.")

                self.__recv_buffer += recv_payload

            expecting_bytes = int.from_bytes(self.__recv_buffer[:self.CONFIG.PAYLOAD_FRAME_LENGTH], byteorder="big")
            expecting_bytes += self.CONFIG.PAYLOAD_FRAME_LENGTH

            while len(self.__recv_buffer) < expecting_bytes:
                recv_payload = self.__recv()
                self.__recv_buffer += recv_payload

            recved = bytes(self.__recv_buffer[self.CONFIG.PAYLOAD_FRAME_LENGTH:expecting_bytes])
            del self.__recv_buffer[:expecting_bytes]

            return recved

    # def handshake(self):
    #     return self.__handshake()

# SOcket Transport, maybe put somewhere else
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
        TransportWrapperMixin.__init__(self)
        self.__wrapped, _ = SSLTransport.wrap(self, wrapped)
        self.__wrapped = typing.cast(SocketTransport, self.__wrapped)

        SocketTransport.__init__(self, self.__wrapped.socket, CONFIG=CONFIG)

        # TODO improve this
        if self.CONFIG.SSL_CONTEXT is None:
            raise ValueError("SSL Context is not initialized. Cannot create a SSL Socket.")
        server_side = self.CONFIG.SSL_CONTEXT.verify_mode != ssl.CERT_REQUIRED
        self.socket = self.CONFIG.SSL_CONTEXT.wrap_socket(self.socket, server_side=server_side)


# TODO write other transport methods (e.g. UDPTransport)




