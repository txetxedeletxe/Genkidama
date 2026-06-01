from genkidama.config import Config
from genkidama.model import Serializable, SerializeT

import dataclasses
from dataclasses import dataclass
import enum
from struct import Struct

import typing
from typing import  Self

class IncompatibleHeaderException(Exception): pass

@dataclass(kw_only=True)
class ConfigHeader(Serializable[SerializeT]):

    MAGIC: str = "GKDM"
    VERSION: tuple[int,int]

    @classmethod
    def from_config(cls: type[Self], config: Config) -> Self:
        return cls(VERSION=config.GENKIDAMA_VERSION)

    def assert_compatible(self, other: "ConfigHeader"):
        if self.MAGIC != other.MAGIC:
            raise IncompatibleHeaderException("MAGIC does not match!")

        if self.VERSION != other.VERSION:
            raise IncompatibleHeaderException("Version numbers do not match!")

# TODO place this somewhere else
@dataclass(kw_only=True)
class SocketConfigHeader(ConfigHeader[bytes]):

    # Flags
    USE_SSL: bool

    # Class Vars
    class Flags(enum.IntFlag):
        USE_SSL = 1

    _STRUCT: typing.ClassVar[Struct] = Struct("!4sBBH") # TODO Abstract this field to the serializable

    @classmethod
    def from_config(cls: type[Self], config: Config) -> Self:
        header = ConfigHeader.from_config(config)
        return cls(USE_SSL=config.SSL_CONTEXT is not None,
                   **dataclasses.asdict(header))

    def assert_compatible(self, other: ConfigHeader):
        if not isinstance(other, SocketConfigHeader):
            raise IncompatibleHeaderException("ConfigHeader type mismatch!") # Maybe this is a different error

        ConfigHeader.assert_compatible(self, other)

        if self.USE_SSL != other.USE_SSL:
            raise IncompatibleHeaderException("SSL config mismatch!")

    @property
    def flags(self) -> "SocketConfigHeader.Flags":
        flags_ = self.Flags(0)

        if self.USE_SSL: flags_ |= self.Flags.USE_SSL

        return flags_

    @classmethod
    def decode(cls: type[Self], data: bytes) -> Self:
        magic,version_M,version_m,flags = cls._STRUCT.unpack(data)

        return cls(MAGIC=bytes.decode(magic),
                   VERSION=(version_M,version_m),
                   USE_SSL=bool(flags & cls.Flags.USE_SSL))

    def encode(self) -> bytes:
        return self._STRUCT.pack(self.MAGIC.encode(), *self.VERSION, self.flags)


