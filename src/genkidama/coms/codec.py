from .requests import Request

from typing import TypeVar, Generic, Protocol

DecodeT = TypeVar("DecodeT")

# TODO document
class Codec(Protocol, Generic[DecodeT]):
    def encode(self, request: Request) -> DecodeT: raise NotImplementedError()
    def decode(self, encoded_request: DecodeT) -> Request: raise NotImplementedError()





