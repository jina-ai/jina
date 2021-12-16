from typing import Union, Optional, TypeVar, Dict, TYPE_CHECKING

from google.protobuf import json_format

from .mixin import DocsPropertyMixin, GroundtruthPropertyMixin
from ..mixin import ProtoTypeMixin
from ...enums import CompressAlgo, RequestType
from ...excepts import BadRequestType
from ...helper import random_identity, typename
from ...proto import jina_pb2

_body_type = set(str(v).lower() for v in RequestType)
_trigger_body_fields = set(
    kk
    for v in [
        jina_pb2.RequestProto.ControlRequestProto,
        jina_pb2.RequestProto.DataRequestProto,
    ]
    for kk in v.DESCRIPTOR.fields_by_name.keys()
)
_trigger_req_fields = set(
    jina_pb2.RequestProto.DESCRIPTOR.fields_by_name.keys()
).difference(_body_type)
_trigger_fields = _trigger_req_fields.union(_trigger_body_fields)

__all__ = ['Request', 'Response']

RequestSourceType = TypeVar(
    'RequestSourceType', jina_pb2.RequestProto, bytes, str, Dict
)

if TYPE_CHECKING:
    from docarray.simple import StructView


class Request(ProtoTypeMixin, DocsPropertyMixin, GroundtruthPropertyMixin):
    """
    :class:`Request` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.jina_pb2.RequestProto` object without working with Protobuf itself.

    A container for serialized :class:`jina_pb2.RequestProto` that only triggers deserialization
    and decompression when receives the first read access to its member.

    It overrides :meth:`__getattr__` to provide the same get/set interface as an
    :class:`jina_pb2.RequestProto` object.

    :param request: The request.
    :param compression_algorithm: The compression algorithm to use.
    :param copy: Copy the request if ``copy`` is True.
    """

    def __init__(
        self,
        request: Optional[
            Union[bytes, dict, str, 'jina_pb2.RequestProto', 'Request']
        ] = None,
        compression_algorithm: Optional[CompressAlgo] = None,
        copy: bool = False,
    ):
        self._buffer = None
        self._compression_algorithm = compression_algorithm
        try:
            if isinstance(request, jina_pb2.RequestProto):
                if copy:
                    self._pb_body = jina_pb2.RequestProto()
                    self._pb_body.CopyFrom(request)
                else:
                    self._pb_body = request
            elif isinstance(request, dict):
                self._pb_body = jina_pb2.RequestProto()
                json_format.ParseDict(request, self._pb_body)
            elif isinstance(request, str):
                self._pb_body = jina_pb2.RequestProto()
                json_format.Parse(request, self._pb_body)
            elif isinstance(request, bytes):
                self._buffer = request
                self._pb_body = None
            elif request is None:
                # make sure every new request has a request id
                self._pb_body = jina_pb2.RequestProto()
                self._pb_body.request_id = random_identity()
            elif request is not None:
                # note ``None`` is not considered as a bad type
                raise ValueError(f'{typename(request)} is not recognizable')
        except Exception as ex:
            raise BadRequestType(
                f'fail to construct a {self.__class__} object from {request}'
            ) from ex

    def __getattr__(self, name: str):
        # https://docs.python.org/3/reference/datamodel.html#object.__getattr__
        if name in _trigger_body_fields:
            return getattr(self.body, name)
        else:
            return getattr(self.proto, name)

    @property
    def is_decompressed(self):
        """Return a boolean indicating if the proto is decompressed

        :return: a boolean indicating if the proto is decompressed
        """
        return self._buffer is None

    @classmethod
    def _from_request(cls, req: 'Request'):
        instance = cls(compression_algorithm=req._compression_algorithm)
        instance._pb_body = req._pb_body
        instance._buffer = req._buffer
        return instance

    @property
    def body(self):
        """
        Return the request type, raise ``ValueError`` if request_type not set.

        :return: body property
        """
        if self._request_type:
            return getattr(self.proto, self._request_type)
        else:
            raise ValueError(f'"request_type" is not set yet')

    @property
    def _request_type(self) -> str:
        return self.proto.WhichOneof('body')

    @property
    def request_type(self) -> Optional[str]:
        """
        Return the request body type, when not set yet, return ``None``.

        :return: request type
        """
        if self._request_type:
            return self.body.__class__.__name__

    def as_typed_request(self, request_type: str):
        """
        Change the request class according to the one_of value in ``body``.

        :param request_type: string representation of the request type
        :return: self
        """
        from .control import ControlRequest
        from .data import DataRequest

        if request_type in _body_type:
            getattr(self._pb_body, request_type).SetInParent()
        rt = request_type.upper()
        if rt.startswith(str(RequestType.DATA)):
            return DataRequest._from_request(self)
        elif rt.startswith(str(RequestType.CONTROL)):
            return ControlRequest._from_request(self)
        else:
            raise TypeError(f'{request_type} is not recognized')

    @staticmethod
    def _decompress(data: bytes, algorithm: Optional[CompressAlgo]) -> bytes:
        if not algorithm:
            return data

        if algorithm == CompressAlgo.LZ4:
            import lz4.frame

            data = lz4.frame.decompress(data)
        elif algorithm == CompressAlgo.BZ2:
            import bz2

            data = bz2.decompress(data)
        elif algorithm == CompressAlgo.LZMA:
            import lzma

            data = lzma.decompress(data)
        elif algorithm == CompressAlgo.ZLIB:
            import zlib

            data = zlib.decompress(data)
        elif algorithm == CompressAlgo.GZIP:
            import gzip

            data = gzip.decompress(data)
        return data

    @property
    def proto(self) -> 'jina_pb2.RequestProto':
        """
        Cast ``self`` to a :class:`jina_pb2.RequestProto`. Laziness will be broken and serialization will be recomputed when calling
        :meth:`SerializeToString`.

        :return: protobuf instance
        """
        if self.is_decompressed:
            return self._pb_body
        else:
            # if not then build one from buffer

            r = jina_pb2.RequestProto()
            _buffer = self._decompress(
                self._buffer,
                self._compression_algorithm,
            )
            r.ParseFromString(_buffer)
            self._pb_body = r
            self._buffer = None
            # # Though I can modify back the envelope, not sure if it is a good design:
            # # My intuition is: if the content is changed dramatically, e.g. from index to control request,
            # # then whatever writes on the envelope should be dropped
            # # depreciated. The only reason to reuse the envelope is saving cost on Envelope(), which is
            # # really a minor minor (and evil) optimization.
            # if self._envelope:
            #     self._envelope.request_type = getattr(r, r.WhichOneof('body')).__class__.__name__
            return r

    def SerializeToString(self) -> bytes:
        """
        Convert serialized data to string.

        :return: serialized request
        """
        if self.is_decompressed:
            return self.proto.SerializePartialToString()
        else:
            # no touch, skip serialization, return original
            return self._buffer

    def as_response(self):
        """
        Return a weak reference of this object but as :class:`Response` object. It gives a more
        consistent semantics on the client.

        :return: `self` as an instance of `Response`
        """
        return Response._from_request(self)

    @property
    def parameters(self) -> 'StructView':
        """Return the `tags` field of this Document as a Python dict

        :return: a Python dict view of the tags.
        """
        # if u get this u need to have it decompressed
        from docarray.simple import StructView

        return StructView(self.proto.parameters)

    @parameters.setter
    def parameters(self, value: Dict):
        """Set the `parameters` field of this Request to a Python dict

        :param value: a Python dict
        """
        self.proto.parameters.Clear()
        self.proto.parameters.update(value)


class Response(Request, DocsPropertyMixin, GroundtruthPropertyMixin):
    """
    Response is the :class:`Request` object returns from the flow. Right now it shares the same representation as
    :class:`Request`. At 0.8.12, :class:`Response` is a simple alias. But it does give a more consistent semantic on
    the client API: send a :class:`Request` and receive a :class:`Response`.

    .. note::
        For now it only exposes `Docs` and `GroundTruth`. Users should very rarely access `Control` commands, so preferably
        not confuse the user by adding `CommandMixin`.
    """
