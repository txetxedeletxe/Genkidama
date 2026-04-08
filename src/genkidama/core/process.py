from genkidama.utils import ForwardingStream, InMemoryPipe

from subprocess import Popen
from io import BufferedIOBase
import io
import threading

from typing import override
import typing


if typing.TYPE_CHECKING:
    from genkidama.core import GenkidamaSession

class Process:
    def __init__(self,
                 id_: int,
                 genkidama_session: "GenkidamaSession",
                 std_endpoints: tuple[BufferedIOBase, BufferedIOBase, BufferedIOBase]):

        self.id = id_
        self.genkidama_session = genkidama_session

        self.stdin, self.stdout, self.stderr = std_endpoints

        # Field to store the exitcode of the process (whatever it means in the host platform)
        # It also serves to check whether the process was waited
        self.exitcode: int | None = None

    # API
    def wait(self) -> int | None: # Add timeout

        if self.exited():
            self.genkidama_session._clean_process(self.id)

            self.stdin.close()
            self.stdout.close()
            self.stderr.close()

        return self.exitcode

    def exited(self) -> bool:
        return self.exitcode is not None

class RemoteProcess(Process):
    def __init__(self, id_: int, genkidama_session: "GenkidamaSession"):
        # Buffers for streams
        stdin_endpoint = ForwardingStream(write_handler=self._write_to_stdin)
        stdout_endpoint, stderr_endpoint = InMemoryPipe(), InMemoryPipe()
        Process.__init__(self, id_, genkidama_session, (stdin_endpoint, stdout_endpoint, stderr_endpoint))

        self.exit_event = threading.Event()

    def _write_to_stdin(self, buffer: bytes):
        self.genkidama_session.donor_session.forward_process_stdin(self.genkidama_session.id, self.id, buffer)

    def wait(self) -> int:
        self.exit_event.wait()
        exitcode = Process.wait(self)

        return typing.cast(int, exitcode)

# LATER
class LocalProcess(Process):
    def __init__(self,
                 id_: int,
                 genkidama_session: "GenkidamaSession",
                 popen: Popen):

        self.popen = popen

        std_endpoints = popen.stdin, popen.stdout, popen.stderr
        std_endpoints = typing.cast(tuple[BufferedIOBase,BufferedIOBase,BufferedIOBase], std_endpoints)

        Process.__init__(self, id_, genkidama_session, std_endpoints)

    @override
    def wait(self) -> int:

        self.exitcode = self.popen.wait()
        exitcode = Process.wait(self)

        return typing.cast(int, exitcode) # We know its not None since we waited
