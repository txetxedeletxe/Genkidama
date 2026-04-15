# TODO improve docstring using PEP
from genkidama.core.process import Process, LocalProcess, RemoteProcess
from genkidama.workers import LikeConsumerProducerPool
from genkidama.config import Configurable

from typing import Generator, Generic
from collections.abc import MutableMapping

import select
import subprocess

import typing

import logging
logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from genkidama.core import DonorSession

ProcessT = typing.TypeVar("ProcessT", bound=Process)

class GenkidamaSession(Configurable, Generic[ProcessT]):

    _PROCESS_FACTORY: type[ProcessT]

    def __init__(self, id_: int, donor_session: "DonorSession"):
        self.id: int = id_
        self.donor_session = donor_session

        self.processes: MutableMapping[int, ProcessT] = {} # Contains processes that have not exited

        self._next_process_id = 0

    def execute(self, script: str) -> ProcessT:
        """Execute the python script in a separate process, return Process (a process handle)."""
        raise NotImplementedError()

    # MOVE this to another API
    def _clean_process(self, process_id: int):
        if process_id not in self.processes:
            raise ValueError(f"process_id ({process_id}) is not registered in the current session.")

        proc = self.processes[process_id]

        if proc.exited():
            self.processes.pop(process_id) # This just removes the process from the session, does not do any waiting


    # Utility private method to create a process
    def _create_process(self, process_id: int | None = None, **kwargs) -> ProcessT:

        if len(self.processes) >= self.CONFIG.MAX_PROCESS_ID:
            raise MemoryError(f"Cannot create process: Exceeded maximum number of active processes ({self.CONFIG.MAX_PROCESS_ID})")

        if process_id is not None:
            process_id = typing.cast(int, process_id)

        else:
            # Find next available id
            process_id = self._next_process_id
            while process_id in self.processes:
                process_id = (process_id+1) % self.CONFIG.MAX_PROCESS_ID
            self._next_process_id = (process_id+1) % self.CONFIG.MAX_PROCESS_ID # Update _next_process_id

        if process_id in self.processes:
            raise ValueError(f"process_id ({process_id}) already exists in this session.")

        proc = self.processes[process_id] = self._PROCESS_FACTORY(process_id, self, **kwargs) # Create process

        return proc


class RemoteGenkidamaSession(GenkidamaSession[RemoteProcess]):

    _PROCESS_FACTORY = RemoteProcess

    def execute(self, script: str) -> RemoteProcess:
        proc = self._create_process()
        self.donor_session.execute(self.id, proc.id, script)

        return proc


# TODO abstract many of the functionalities
class LocalGenkidamaSession(GenkidamaSession[LocalProcess], LikeConsumerProducerPool[int]):

    _PROCESS_FACTORY = LocalProcess

    def __init__(self, id_: int, donor_session: "DonorSession"):
        GenkidamaSession.__init__(self, id_, donor_session)
        LikeConsumerProducerPool.__init__(self,
                                          producer_count=1, # "produce" is implemented to work with a single thread
                                          consumer_count=self.CONFIG.SESSION_POLLING_WORKERS)

        # TODO Maybe abstract some of this logic
        self._poll: select.poll = select.poll()
        self._fd2process: MutableMapping[int, tuple[LocalProcess, int]] = {}


    def execute(self, script: str, process_id: int | None = None) -> LocalProcess:

        # TODO Abstract process creation? put popen logic inside LocalProcess
        logger.debug(f"Executing process with id: {process_id}")
        popen = subprocess.Popen([*self.CONFIG.EXEC_PROGRAM_ARGS, script],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 close_fds=True)
        proc = self._create_process(process_id, popen=popen)

        # Register file descriptors
        stdout_fd, stderr_fd = proc.stdout.fileno(), proc.stderr.fileno()

        self._fd2process[stdout_fd] = (proc, 1) # TODO find a more elegant codification
        self._fd2process[stderr_fd] = (proc, 2)

        self._poll.register(stdout_fd)
        self._poll.register(stderr_fd)

        return proc

    # Consumer producer code
    def produce(self) -> Generator[int]:
        polled = self._poll.poll(self.CONFIG.SESSION_POLLING_TIMEOUT) # TODO add a self pipe to interrupt polling
        if polled:
            fds, _ = zip(*polled)
            for fd in fds:
                self._poll.unregister(fd)
                yield fd

    def consume(self, fd: int):

        proc, stream_fd = self._fd2process[fd]
        stream = proc.stdout if stream_fd == 1 else proc.stderr

        content = stream.read1()
        match stream_fd:
            case 1: self.donor_session.forward_process_stdout(self.id, proc.id, content)
            case 2: self.donor_session.forward_process_stderr(self.id, proc.id, content)

        if not content:
            self._fd2process.pop(fd)

            if (proc.stdout.fileno() not in self._fd2process and
                proc.stderr.fileno() not in self._fd2process):

                exitcode = proc.wait() # TODO wait on a different thread
                self.donor_session.exit_process(self.id, proc.id, exitcode)

        else:
            self._poll.register(fd)




