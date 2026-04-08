from genkidama.core.genkidama_session import GenkidamaSession, LocalGenkidamaSession, RemoteGenkidamaSession
from genkidama.coms.requests import *
from genkidama.coms import Endpoint
from genkidama.config import Configurable

from typing import Generic
from collections.abc import MutableMapping

import typing
import requests

SessionT = typing.TypeVar("SessionT", bound=GenkidamaSession)

class DonorSession(Endpoint, Configurable, Generic[SessionT]):

    _GENKIDAMA_SESSION_FACTORY : type[SessionT]

    def __init__(self, mirror_endpoint: Endpoint):
        Endpoint.__init__(self, mirror_endpoint)

        master_session: SessionT = self._GENKIDAMA_SESSION_FACTORY(self.CONFIG.MASTER_SESSION_ID, self)
        self.genkidama_sessions: MutableMapping[int, SessionT] = {master_session.id: master_session}

    @property
    def master_session(self):
        return self.genkidama_sessions[self.CONFIG.MASTER_SESSION_ID]

    # API: Comprised of most of the requests that can be made to the Donor
    def execute(self, genkidama_session_id: int, process_id: int, script: str):
        raise NotImplementedError()

    def exit_process(self, genkidama_session_id: int, process_id: int, exitcode: int):
        raise NotImplementedError()

    def forward_process_stdin(self, genkidama_session_id: int, process_id: int, content: bytes):
        raise NotImplementedError()

    def forward_process_stdout(self, genkidama_session_id: int, process_id: int, content: bytes):
        raise NotImplementedError()

    def forward_process_stderr(self, genkidama_session_id: int, process_id: int, content: bytes):
        raise NotImplementedError()

    def forward_request(self, request: Request): # TODO add request filters to avoid bugs
        match request.REQUEST_TYPE_ID:
            case RequestTypeId.ExecutionRequest:
                request = typing.cast(ExecutionRequest, request)
                self.execute(request.genkidama_session_id, request.process_id, request.script)

            case RequestTypeId.ExitProcessRequest:
                request = typing.cast(ExitProcessRequest, request)
                self.exit_process(request.genkidama_session_id, request.process_id, request.exitcode)

            case RequestTypeId.ForwardStdinRequest:
                request = typing.cast(ForwardStdinRequest, request)
                self.forward_process_stdin(request.genkidama_session_id, request.process_id, request.content)

            case RequestTypeId.ForwardStdoutRequest:
                request = typing.cast(ForwardStdoutRequest, request)
                self.forward_process_stdout(request.genkidama_session_id, request.process_id, request.content)

            case RequestTypeId.ForwardStderrRequest:
                request = typing.cast(ForwardStderrRequest, request)
                self.forward_process_stderr(request.genkidama_session_id, request.process_id, request.content)


class RemoteDonorSession(DonorSession[RemoteGenkidamaSession]):

    _GENKIDAMA_SESSION_FACTORY = RemoteGenkidamaSession

    # Remote API
    def execute(self, genkidama_session_id: int, process_id: int, script: str):
        request = ExecutionRequest(genkidama_session_id, process_id, script)
        self.mirror_endpoint.forward_request(request)

    def forward_process_stdin(self, genkidama_session_id: int, process_id: int, content: bytes):
        request = ForwardStdinRequest(genkidama_session_id, process_id, content)
        self.mirror_endpoint.forward_request(request)

    # LocalAPI
    def exit_process(self, genkidama_session_id: int, process_id: int, exitcode: int):
        proc = self.genkidama_sessions[genkidama_session_id].processes[process_id]
        proc.exitcode = exitcode
        proc.exit_event.set()

    def forward_process_stdout(self, genkidama_session_id: int, process_id: int, content: bytes):
        proc = self.genkidama_sessions[genkidama_session_id].processes[process_id]
        proc.stdout.write(content)

    def forward_process_stderr(self, genkidama_session_id: int, process_id: int, content: bytes):
        proc = self.genkidama_sessions[genkidama_session_id].processes[process_id]
        proc.stderr.write(content) # Flush?


class LocalDonorSession(DonorSession[LocalGenkidamaSession]):
    _GENKIDAMA_SESSION_FACTORY = LocalGenkidamaSession

    def __init__(self, mirror_endpoint: Endpoint):
        DonorSession.__init__(self, mirror_endpoint)

    def start(self):
        for session in self.genkidama_sessions.values():
            session.start()

    # API
    def execute(self, genkidama_session_id: int, process_id: int, script: str):
        self.genkidama_sessions[genkidama_session_id].execute(script, process_id)

    def forward_process_stdin(self, genkidama_session_id: int, process_id: int, content: bytes):
        proc = self.genkidama_sessions[genkidama_session_id].processes[process_id]
        proc.stdin.write(content)
        proc.stdin.flush() # TODO abstract this

    def exit_process(self, genkidama_session_id: int, process_id: int, exitcode: int):
        request = ExitProcessRequest(genkidama_session_id, process_id, exitcode)
        self.mirror_endpoint.forward_request(request)

    def forward_process_stdout(self, genkidama_session_id: int, process_id: int, content: bytes):
        request = ForwardStdoutRequest(genkidama_session_id, process_id, content)
        self.mirror_endpoint.forward_request(request)

    def forward_process_stderr(self, genkidama_session_id: int, process_id: int, content: bytes):
        request = ForwardStderrRequest(genkidama_session_id, process_id, content)
        self.mirror_endpoint.forward_request(request)






