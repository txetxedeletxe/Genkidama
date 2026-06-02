from genkidama.coms.transport import Transport

import os

import types
from typing import TypeVar,Protocol, Callable, Generic, Self

TransportT = TypeVar("TransportT", bound=Transport, covariant=True)

class Server(Protocol, Generic[TransportT]):
    def accept(self, *, handshake=True) -> TransportT: raise NotImplementedError()


ServerT = TypeVar("ServerT", bound=Server, covariant=True)
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




