"""Utilities to facilitate Inter-Process Communication (IPC) operations in a pythonic and platform independent way.""" # TODO esure platform independece
from collections.abc import Buffer
from io import BufferedIOBase
from typing import Callable

import sys

import queue
import threading

import typing

class InMemoryPipe(BufferedIOBase):
    def __init__(self):
        self._queue: queue.Queue[bytes] = queue.Queue()
        self._buffer = bytearray()

        self._lock = threading.RLock()

    def read(self, size: int | None = -1, /) -> bytes:
        if size is None or size < 0: size = sys.maxsize
        with self._lock:
            while len(self._buffer) < size and not self._queue.empty():
                read = self._queue.get()
                self._buffer += read

                if not read:
                    break

            to_return = bytes(self._buffer[:size])
            del self._buffer[:size]

            return to_return

    def write(self, buffer: Buffer, /) -> int:
        buffer = typing.cast(bytes, buffer)
        self._queue.put(buffer)

        return len(buffer)

class ForwardingStream(BufferedIOBase):
    def __init__(self, write_handler: Callable[[bytes], None]):
        self.write_handler = write_handler

    def write(self, buffer: Buffer, /) -> int:
        buffer = typing.cast(bytes, buffer)
        self.write_handler(buffer)

        return len(buffer)


