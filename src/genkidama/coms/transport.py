from genkidama.config import Config, Configurable

import threading

import types
from typing import Protocol, Generic, Self, TypeVar

MediaT = TypeVar("MediaT")
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

