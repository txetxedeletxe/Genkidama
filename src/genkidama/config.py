from dataclasses import dataclass, field

import sys

@dataclass(eq=False, repr=False, kw_only=True)
class Config: # TODO optimize config


    SERVER_PORT = 9001

    PAYLOAD_FRAME_LENGTH: int = 4

    SOCKET_BUFFERSIZE: int = 1024

    TERMINAL_ENDPOINT_WORKERS: int = 1
    SESSION_POLLING_WORKERS: int = 1
    SESSION_POLLING_TIMEOUT: int = 50 # time in ms

    EXEC_PROGRAM_ARGS = (sys.executable, "-c")

    # PROTOCOL
    ## MASTER GENKIDAMA SESSION ID (read-only constant)
    _MASTER_SESSION_ID: int = field(default=0, init=False)

    @property
    def MASTER_SESSION_ID(self) -> int: return self._MASTER_SESSION_ID

    ## LENGTH OF IDENTIFIERS IN BYTES
    REQUEST_ID_LENGTH: int = 2
    SESSION_ID_LENGTH: int = 1
    PROCESS_ID_LENGTH: int = 2

    ## MAXIMUM VALUE OF IDENTIFIERS
    def max_id(self, id_length: int) -> int:
        return 1 << 8*id_length

    @property
    def MAX_REQUEST_ID(self) -> int: return self.max_id(self.REQUEST_ID_LENGTH)

    @property
    def MAX_SESSION_ID(self) -> int: return self.max_id(self.SESSION_ID_LENGTH)

    @property
    def MAX_PROCESS_ID(self) -> int: return self.max_id(self.PROCESS_ID_LENGTH)


DEFAULTS = Config()
class Configurable:
    CONFIG: Config = DEFAULTS # TODO add constructor for ad-hoc configuration
