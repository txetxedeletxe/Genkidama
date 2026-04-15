from genkidama.config import Configurable

from enum import IntEnum, unique
from dataclasses import dataclass, field
from typing import ClassVar, TypeVar
from collections.abc import Set

@unique
class RequestTypeId(IntEnum):
    # TODO add ping request
    ExecutionRequest = 1
    ForwardStdinRequest = 2
    ForwardStdoutRequest = 3
    ForwardStderrRequest = 4
    ExitProcessRequest = 5


@dataclass
class Request(Configurable):

    @staticmethod
    def _generate_request_id() -> int:
        request_id = Request._next_request_id
        Request._next_request_id = (Request._next_request_id + 1) % Request.CONFIG.MAX_REQUEST_ID

        return request_id

    # Fields
    request_id: int = field(default_factory=_generate_request_id, kw_only=True)

    # ClassVars
    REQUEST_TYPE_ID: ClassVar[RequestTypeId]
    SUB_REQUEST_TYPE_IDS: ClassVar[Set[RequestTypeId]] = frozenset()

    _next_request_id: ClassVar[int] = 0

    # Instance methods
    def __post_init__(self):
        self._validate()

    def _validate(self): # TODO make a custom error for this case
        if not (0 <= self.request_id < self.CONFIG.MAX_PROCESS_ID):
            raise ValueError(f"request_id ({self.request_id}) cannot be represented within the length limit ({self.CONFIG.REQUEST_ID_LENGTH} bytes).")

T = TypeVar("T", bound=Request)
def subscribe_request_type(cls: type[T]) -> type[T]:

        cls.SUB_REQUEST_TYPE_IDS = frozenset() # This is making a copy

        if not hasattr(cls, "REQUEST_TYPE_ID"):
            return cls

        # Propagate upwards
        for c in cls.mro():
            if issubclass(c, Request):
                c.SUB_REQUEST_TYPE_IDS = c.SUB_REQUEST_TYPE_IDS | frozenset((cls.REQUEST_TYPE_ID,))

        return cls

@subscribe_request_type
@dataclass
class GenkidamaSessionRequest(Request):
    # Fields
    genkidama_session_id: int

    def _validate(self):
        Request._validate(self)
        if not (0 <= self.genkidama_session_id < self.CONFIG.MAX_SESSION_ID):
            raise ValueError(f"genkidama_session_id ({self.genkidama_session_id}) cannot be represented within the length limit ({self.CONFIG.SESSION_ID_LENGTH} bytes).")

@subscribe_request_type
@dataclass
class ProcessRequest(GenkidamaSessionRequest): # Base dataclass that adds identifiers for process and session
    # Fields
    process_id: int

    def _validate(self):
        GenkidamaSessionRequest._validate(self)
        if not (0 <= self.process_id < self.CONFIG.MAX_PROCESS_ID):
            raise ValueError(f"process_id ({self.process_id}) cannot be represented within the length limit ({self.CONFIG.PROCESS_ID_LENGTH} bytes).")

@subscribe_request_type
@dataclass
class ExecutionRequest(ProcessRequest):
    # Fields
    script: str

    # ClassVars
    REQUEST_TYPE_ID = RequestTypeId.ExecutionRequest

@subscribe_request_type
@dataclass
class ExitProcessRequest(ProcessRequest):
    # Fields
    exitcode: int

    # ClassVars
    REQUEST_TYPE_ID = RequestTypeId.ExitProcessRequest

@subscribe_request_type
@dataclass
class ForwardStreamRequest(ProcessRequest):
    content: bytes

@subscribe_request_type
@dataclass
class ForwardStdinRequest(ForwardStreamRequest):
    REQUEST_TYPE_ID = RequestTypeId.ForwardStdinRequest

@subscribe_request_type
@dataclass
class ForwardStdoutRequest(ForwardStreamRequest):
    REQUEST_TYPE_ID = RequestTypeId.ForwardStdoutRequest

@subscribe_request_type
@dataclass
class ForwardStderrRequest(ForwardStreamRequest):
    REQUEST_TYPE_ID = RequestTypeId.ForwardStderrRequest
