from dataclasses import dataclass, field

import ssl
import sys

import typing
import enum

import logging
logger = logging.getLogger(__name__)


@dataclass(eq=False, repr=False, kw_only=True)
class Config: # TODO optimize config (separate different configs)

    # Version
    _GENKIDAMA_VERSION: typing.ClassVar[tuple[int,int]] = 0,1
    @property
    def GENKIDAMA_VERSION(self): return self._GENKIDAMA_VERSION

    # Connection
    SERVER_PORT: int = 9000
    SSL_CONTEXT: ssl.SSLContext | None = None

    # Transport
    SOCKET_BUFFERSIZE: int = 1024
    PAYLOAD_FRAME_LENGTH: int = 4 # Stream transport framing

    # Workers
    TERMINAL_ENDPOINT_WORKERS: int = 1
    SESSION_POLLING_WORKERS: int = 1
    SESSION_POLLING_TIMEOUT: int = 50 # time in ms

    # Execution # TODO improve this
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

    # Methods
    def load_donor_ssl_context(self, cafile: str | None = None, capath: str | None = None):

        self.SSL_CONTEXT = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
        self.SSL_CONTEXT.check_hostname = False
        self.SSL_CONTEXT.verify_mode = ssl.CERT_REQUIRED
        self.SSL_CONTEXT.load_verify_locations(cafile, capath)

    def load_kaio_ssl_context(self, certfile: str, keyfile: str | None = None):

        self.SSL_CONTEXT = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_SERVER)
        self.SSL_CONTEXT.load_cert_chain(certfile,keyfile)


DEFAULTS = Config()
class Configurable:
    CONFIG: Config = DEFAULTS

    def __init__(self, *, CONFIG: Config | None = None):
        self.CONFIG = self.CONFIG if CONFIG is None else CONFIG

