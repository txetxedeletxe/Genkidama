from genkidama.config import Configurable

import socket
import threading

import typing
from typing import Generic, Self

MediaT = typing.TypeVar("MediaT")
class Transport(Generic[MediaT]):
    def send(self, payload: MediaT): raise NotImplementedError()
    def recv(self) -> MediaT: raise NotImplementedError()
    # TODO implement close

class TransportWrapperMixin(Transport[MediaT], Generic[MediaT]):
    def __init__(self, wrapped: Transport[MediaT] | None = None):
        self._wrapped = self if wrapped is None else typing.cast(Transport[MediaT], wrapped)

        # Swap the wrapped recv and send for the wrapping ones
        self.recv, self._recv = self._recv, self._wrapped.recv
        self.send, self._send = self._send, self._wrapped.send

    def _send(self, payload: MediaT): raise NotImplementedError()
    def _recv(self) -> MediaT: raise NotImplementedError()

class BinaryStreamTransport(TransportWrapperMixin[bytes], Configurable):
    def __init__(self, wrapped: Transport[bytes] | None = None):
        TransportWrapperMixin.__init__(self, wrapped)

        self._recv_buffer = bytearray()
        self._lock = threading.RLock()

    def _send(self, payload: bytes):
        payload_length = len(payload)
        framed_payload = payload_length.to_bytes(self.CONFIG.PAYLOAD_FRAME_LENGTH) + payload

        self._send(framed_payload)


    def _recv(self) -> bytes:
        with self._lock:
            while len(self._recv_buffer) < self.CONFIG.PAYLOAD_FRAME_LENGTH:

                recv_payload = self._recv()
                if not recv_payload: # Connection closed
                    raise ConnectionResetError("Connection closed by peer.")

                self._recv_buffer += recv_payload

            expecting_bytes = int.from_bytes(self._recv_buffer[:self.CONFIG.PAYLOAD_FRAME_LENGTH])
            expecting_bytes += self.CONFIG.PAYLOAD_FRAME_LENGTH

            while len(self._recv_buffer) < expecting_bytes:
                recv_payload = self._recv()
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

# TODO write other transport methods (e.g. UDPTransport)




