from genkidama.coms import Request, Transport, Codec
from genkidama.config import Configurable
from genkidama.workers import LikeWorkerPool, Warden, WorkFinishedException

import threading

import typing
from typing import Generic

import logging
logger = logging.getLogger(__name__)

T = typing.TypeVar("T")

class Endpoint:
    def __init__(self, mirror_endpoint: "Endpoint"):
        self.mirror_endpoint = mirror_endpoint

    def forward_request(self, request: Request):
        raise NotImplementedError()


class TerminalEndpoint(Endpoint, LikeWorkerPool, Configurable, Generic[T]):
    def __init__(self, codec: Codec[T], transport: Transport[T]):
        LikeWorkerPool.__init__(self, worker_count=self.CONFIG.TERMINAL_ENDPOINT_WORKERS)

        self.codec: Codec[T] = codec
        self.transport: Transport[T] = transport

        self._lock = threading.RLock()
        self._warden = Warden()

    def forward_request(self, request: Request):
        encoded_request = self.codec.encode(request)
        self.transport.send(encoded_request)

        logger.debug(f"Request Sent: {request}")

    def do_work(self): # Add thread safety where needed
        with self._lock:

            try:
                encoded_request = self.transport.recv()
            except ConnectionResetError:
                raise WorkFinishedException()

            request = self.codec.decode(encoded_request)

            lock = self._warden.get_lock(request)
            lock.acquire()


        logger.debug(f"Request Received: {request}")

        self.mirror_endpoint.forward_request(request)
        lock.release()

        logger.debug(f"Request Handled: {request}")



