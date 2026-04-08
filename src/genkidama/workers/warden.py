from genkidama.coms.requests import Request, RequestTypeId, ProcessRequest

from collections import defaultdict
from collections.abc import Mapping, Sequence
import typing

from threading import Lock
import threading


class DummyLock:
    def acquire(self, *args, **kwargs) -> bool:
        return True

    def release(self) -> None:
        return

class Warden:
    def __init__(self):
        self.lock_map: Mapping[tuple[int,...], Lock] = defaultdict(Lock)

    def get_lock(self, request: Request) -> Lock | DummyLock:
        if request.REQUEST_TYPE_ID in ProcessRequest.SUB_REQUEST_TYPE_IDS:
            request = typing.cast(ProcessRequest, request)
            return self.lock_map[(request.genkidama_session_id, request.process_id)]

        return DummyLock()


