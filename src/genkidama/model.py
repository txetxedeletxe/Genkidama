from typing import Protocol, TypeVar, Generic, Self

SerializeT = TypeVar("SerializeT")
class Serializable(Protocol, Generic[SerializeT]):
    @classmethod
    def decode(cls: type[Self], data: SerializeT) -> Self:
        raise NotImplementedError()

    def encode(self) -> SerializeT:
        raise NotImplementedError()


class Validable(Protocol):
    def validate(self): raise NotImplementedError() # TODO add custom errors
