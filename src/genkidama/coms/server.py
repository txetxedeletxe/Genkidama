from genkidama.model import Closeable
from genkidama.coms.transport import Transport

import os

import types
from typing import TypeVar,Protocol, Callable, Generic, Self

TransportT = TypeVar("TransportT", bound=Transport, covariant=True)

class Server(Closeable, Protocol, Generic[TransportT]):
    def accept(self, *, handshake=True) -> TransportT: raise NotImplementedError()

ServerT = TypeVar("ServerT", bound=Server, covariant=True)
class ServerWrapperMixin(Server[TransportT], Generic[ServerT, TransportT]):

    @classmethod
    def wrap(cls: type[Self], self: Self, wrapped: ServerT | None = None):
        wrapped_ = self if wrapped is None else wrapped

        self.accept, accept_return = types.MethodType(cls.accept, self), wrapped_.accept

        self.close, close_return = types.MethodType(cls.close, self), wrapped_.close

        return wrapped_, (accept_return, close_return)

    def __init__(self, wrapped: ServerT | None = None) -> None:
        self.__wrapped, (self.__accept, self.__close) = ServerWrapperMixin.wrap(self, wrapped)

    def accept(self, *, handshake=True) -> TransportT: return self.__accept(handshake=handshake)
    def close(self): return self.__close()


class ForkingServer(ServerWrapperMixin[Server[TransportT], TransportT], Generic[TransportT]):
    def __init__(self, wrapped: Server[TransportT] | None = None):
        ServerWrapperMixin.__init__(self, wrapped)
        self.__wrapped, (self.__accept, self.__close) = ForkingServer[TransportT].wrap(self, wrapped)

    def accept(self, *, handshake=True):
        while True: # TODO add a stopping mechanism # TODO Add max connections
            transport = self.__accept(handshake=False)

            if os.fork() == 0: # child
                self.__close()

                if handshake: transport.handshake()
                return transport

            else:
                transport.close()




