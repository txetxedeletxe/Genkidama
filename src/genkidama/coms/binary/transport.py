from genkidama.config import Config, Configurable
from genkidama.coms.transport import Transport, TransportWrapperMixin

import threading

class BinaryStreamTransport(TransportWrapperMixin[bytes], Configurable):
    def __init__(self, wrapped: Transport[bytes] | None = None, *, CONFIG: Config | None = None):
        TransportWrapperMixin.__init__(self, wrapped)
        self.__wrapped, (self.__send, self.__recv, *_) = BinaryStreamTransport.wrap(self, wrapped)

        self.__recv_buffer = bytearray() # TODO Change this for a circular buffer
        self.__lock = threading.RLock()

        Configurable.__init__(self, CONFIG=CONFIG)

    # TODO find a way to use weak references instead of copying the buffers
    def send(self, payload: bytes):
        payload_length = len(payload)
        framed_payload = payload_length.to_bytes(self.CONFIG.PAYLOAD_FRAME_LENGTH) + payload

        self.__send(framed_payload)

    def recv(self) -> bytes:
        with self.__lock:
            while len(self.__recv_buffer) < self.CONFIG.PAYLOAD_FRAME_LENGTH:

                recv_payload = self.__recv()
                if not recv_payload: # Connection closed
                    raise ConnectionResetError("Connection closed by peer.")

                self.__recv_buffer += recv_payload

            expecting_bytes = int.from_bytes(self.__recv_buffer[:self.CONFIG.PAYLOAD_FRAME_LENGTH], byteorder="big")
            expecting_bytes += self.CONFIG.PAYLOAD_FRAME_LENGTH

            while len(self.__recv_buffer) < expecting_bytes:
                recv_payload = self.__recv()
                self.__recv_buffer += recv_payload

            recved = bytes(self.__recv_buffer[self.CONFIG.PAYLOAD_FRAME_LENGTH:expecting_bytes])
            del self.__recv_buffer[:expecting_bytes]

            return recved
