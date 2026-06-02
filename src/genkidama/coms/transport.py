from genkidama.model import Closeable

import types
from typing import Protocol, Generic, Self, TypeVar

MediaT = TypeVar("MediaT")
class Transport(Closeable, Protocol, Generic[MediaT]):
    def send(self, payload: MediaT): raise NotImplementedError()
    def recv(self) -> MediaT: raise NotImplementedError()

    def handshake(self): raise NotImplementedError


class TransportWrapperMixin(Transport[MediaT], Generic[MediaT]):

    @classmethod
    def wrap(cls: type[Self], self: Self, wrapped: Transport[MediaT] | None = None):
        wrapped_ = self if wrapped is None else wrapped

        self.send, send_return = types.MethodType(cls.send,self), wrapped_.send
        self.recv, recv_return = types.MethodType(cls.recv,self), wrapped_.recv
        self.handshake, handshake_return = types.MethodType(cls.handshake,self), wrapped_.handshake

        self.close, close_return = types.MethodType(cls.close,self), wrapped_.close


        return wrapped_, (send_return, recv_return, handshake_return, close_return)

    def __init__(self, wrapped: Transport[MediaT] | None = None):
        self.__wrapped, (self.__send, self.__recv, self.__handshake, self.__close) = TransportWrapperMixin.wrap(self, wrapped)

    def send(self, payload: MediaT): return self.__send(payload)
    def recv(self) -> MediaT: return self.__recv()
    def handshake(self): return self.__handshake()

    def close(self): return self.__close()


