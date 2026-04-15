from dataclasses import dataclass, field

import sys

import typing

import logging
logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    import ssl

@dataclass(eq=False, repr=False, kw_only=True)
class Config: # TODO optimize config (separate different configs)

    SERVER_PORT: int = 9000
    SSL_CONTEXT: "ssl.SSLContext | None" = None

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

    # Methods
    def load_donor_ssl_context(self, cafile: str | None = None, capath: str | None = None):

        import ssl

        self.SSL_CONTEXT = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
        self.SSL_CONTEXT.check_hostname = False
        self.SSL_CONTEXT.verify_mode = ssl.CERT_REQUIRED
        self.SSL_CONTEXT.load_verify_locations(cafile, capath)

    def load_kaio_ssl_context(self, certfile: str, keyfile: str | None = None):

        import ssl

        self.SSL_CONTEXT = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_SERVER)
        self.SSL_CONTEXT.load_cert_chain(certfile, keyfile)


DEFAULTS = Config()
class Configurable:
    CONFIG: Config = DEFAULTS # TODO add constructor for ad-hoc configuration

