from typing import Dict, Optional, TypeVar

from google.protobuf import json_format

from jina.excepts import BadRequestType
from jina.helper import typename
from jina.proto import jina_pb2
from jina.types.mixin import ProtoTypeMixin

StatusSourceType = TypeVar('StatusSourceType', jina_pb2.StatusProto, str, Dict, bytes)


class StatusMessage(ProtoTypeMixin):
    """Represents a Status message used for health check of the Flow"""

    def __init__(
        self,
        status_object: Optional[StatusSourceType] = None,
    ):
        self._pb_body = jina_pb2.StatusProto()
        try:
            if isinstance(status_object, jina_pb2.StatusProto):
                self._pb_body = status_object
            elif isinstance(status_object, dict):
                json_format.ParseDict(status_object, self._pb_body)
            elif isinstance(status_object, str):
                json_format.Parse(status_object, self._pb_body)
            elif isinstance(status_object, bytes):
                self._pb_body.ParseFromString(status_object)
            elif status_object is not None:
                # note ``None`` is not considered as a bad type
                raise ValueError(f'{typename(status_object)} is not recognizable')
            else:
                self._pb_body = jina_pb2.StatusProto()
        except Exception as ex:
            raise BadRequestType(
                f'fail to construct a {self.__class__} object from {status_object}'
            ) from ex

    def set_exception(self, ex: Exception):
        """Set exception information into the Status Message

        :param ex: The Exception to be filled
        """
        import traceback

        self.proto.code = jina_pb2.StatusProto.ERROR
        self.proto.description = repr(ex)
        self.proto.exception.name = ex.__class__.__name__
        self.proto.exception.args.extend([str(v) for v in ex.args])
        self.proto.exception.stacks.extend(
            traceback.format_exception(type(ex), value=ex, tb=ex.__traceback__)
        )

    def set_code(self, code):
        """Set the code of the Status Message

        :param code: The code to be added
        """
        self.proto.code = code
