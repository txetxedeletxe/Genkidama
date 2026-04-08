from genkidama.coms.requests import *
from genkidama.config import Configurable

from typing import Generic
import typing

DecodeT = typing.TypeVar("DecodeT")

# TODO document
class Codec(Configurable, Generic[DecodeT]):
    def encode(self, request: Request) -> DecodeT: raise NotImplementedError()
    def decode(self, encoded_request: DecodeT) -> Request: raise NotImplementedError()

class BinaryCodec(Codec[bytes]):
    def encode(self, request: Request) -> bytes:

        byte_buffer = bytearray()
        byte_buffer += request.request_id.to_bytes(self.CONFIG.REQUEST_ID_LENGTH)

        request_type = request.REQUEST_TYPE_ID
        byte_buffer += request_type.to_bytes()

        # Add ids # TODO change lookup strategy
        if request_type in GenkidamaSessionRequest.SUB_REQUEST_TYPE_IDS:
            request = typing.cast(GenkidamaSessionRequest, request)
            byte_buffer += request.genkidama_session_id.to_bytes(self.CONFIG.SESSION_ID_LENGTH)

        if request_type in ProcessRequest.SUB_REQUEST_TYPE_IDS:
            request = typing.cast(ProcessRequest, request)
            byte_buffer += request.process_id.to_bytes(self.CONFIG.PROCESS_ID_LENGTH)

        # Check if it is a forward stream request
        if request_type in ForwardStreamRequest.SUB_REQUEST_TYPE_IDS:
            request = typing.cast(ForwardStreamRequest, request)
            byte_buffer += request.content

        else:

            match request_type:
                case RequestTypeId.ExecutionRequest:
                    request = typing.cast(ExecutionRequest, request)
                    byte_buffer += request.script.encode()

                case RequestTypeId.ExitProcessRequest:
                    request = typing.cast(ExitProcessRequest, request)
                    byte_buffer += request.exitcode.to_bytes()

        return bytes(byte_buffer)

    # TODO improve this
    def decode(self, encoded_request: bytes) -> Request:

        span_start, span_end = 0, self.CONFIG.REQUEST_ID_LENGTH
        request_id = int.from_bytes(encoded_request[span_start:span_end])

        span_start, span_end = span_end, span_end+1
        request_type = RequestTypeId(int.from_bytes(encoded_request[span_start:span_end]))

        # Add ids
        genkidama_session_id, process_id = 0, 0
        if request_type in GenkidamaSessionRequest.SUB_REQUEST_TYPE_IDS:
            span_start, span_end = span_end, span_end + self.CONFIG.SESSION_ID_LENGTH
            genkidama_session_id = int.from_bytes(encoded_request[span_start:span_end])

        if request_type in ProcessRequest.SUB_REQUEST_TYPE_IDS:
            span_start, span_end = span_end, span_end + self.CONFIG.PROCESS_ID_LENGTH
            process_id = int.from_bytes(encoded_request[span_start:span_end])

        content = bytes()
        if request_type in ForwardStreamRequest.SUB_REQUEST_TYPE_IDS:
            content = encoded_request[span_end:]


        match request_type:
            case RequestTypeId.ExecutionRequest:
                script = encoded_request[span_end:].decode()
                return ExecutionRequest(genkidama_session_id, process_id, script, request_id=request_id)

            case RequestTypeId.ExitProcessRequest:
                exitcode = int.from_bytes(encoded_request[span_end:])
                return ExitProcessRequest(genkidama_session_id, process_id, exitcode, request_id=request_id)

            case RequestTypeId.ForwardStdinRequest:
                return ForwardStdinRequest(genkidama_session_id, process_id, content, request_id=request_id)

            case RequestTypeId.ForwardStdoutRequest:
                return ForwardStdoutRequest(genkidama_session_id, process_id, content, request_id=request_id)

            case RequestTypeId.ForwardStderrRequest:
                return ForwardStderrRequest(genkidama_session_id, process_id, content, request_id=request_id)


# TODO fix this
__all__ = ["Codec", "BinaryCodec"]



