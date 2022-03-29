import copy
from typing import Dict, Optional, TypeVar

from docarray import DocumentArray
from google.protobuf import json_format

from jina.excepts import BadRequestType
from jina.helper import cached_property, random_identity, typename
from jina.proto import jina_pb2
from jina.types.request import Request

RequestSourceType = TypeVar(
    'RequestSourceType', jina_pb2.DataRequestProto, str, Dict, bytes
)


class DataRequest(Request):
    """Represents a DataRequest used for exchanging DocumentArrays to and within a Flow"""

    class _DataContent:
        def __init__(self, content: 'jina_pb2.DataRequestProto.DataContentProto'):
            self._content = content
            self._loaded_doc_array = None

        @property
        def docs(self) -> 'DocumentArray':
            """Get the :class: `DocumentArray` with sequence `data.docs` as content.

            .. # noqa: DAR201"""
            if not self._loaded_doc_array:
                if self._content.WhichOneof('documents') == 'docs_bytes':
                    self._loaded_doc_array = DocumentArray.from_bytes(
                        self._content.docs_bytes
                    )
                else:
                    self._loaded_doc_array = DocumentArray.from_protobuf(
                        self._content.docs
                    )

            return self._loaded_doc_array

        @docs.setter
        def docs(self, value: DocumentArray):
            """Override the DocumentArray with the provided one

            :param value: a DocumentArray
            """
            self.set_docs_convert_arrays(value, None)

        def set_docs_convert_arrays(
            self, value: DocumentArray, ndarray_type: Optional[str] = None
        ):
            """ " Convert embedding and tensor to given type, then set DocumentArray

            :param value: a DocumentArray
            :param ndarray_type: type embedding and tensor will be converted to
            """
            if value is not None:
                self._loaded_doc_array = None
                self._content.docs.CopyFrom(
                    value.to_protobuf(ndarray_type=ndarray_type)
                )

        @property
        def docs_bytes(self) -> bytes:
            """Get the :class: `DocumentArray` with sequence `data.docs` as content.

            .. # noqa: DAR201"""
            return self._content.docs_bytes

        @docs_bytes.setter
        def docs_bytes(self, value: bytes):
            """Override the DocumentArray with the provided one

            :param value: a DocumentArray
            """
            if value:
                self._loaded_doc_array = None
                self._content.docs_bytes = value

    """
    :class:`DataRequest` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.jina_pb2.DataRequestProto` object without working with Protobuf itself.

    A container for serialized :class:`jina_pb2.DataRequestProto` that only triggers deserialization
    and decompression when receives the first read access to its member.

    It overrides :meth:`__getattr__` to provide the same get/set interface as an
    :class:`jina_pb2.DataRequestProto` object.

    :param request: The request.
    """

    def __init__(
        self,
        request: Optional[RequestSourceType] = None,
    ):
        self.buffer = None
        try:
            if isinstance(request, jina_pb2.DataRequestProto):
                self._pb_body = request
            elif isinstance(request, dict):
                self._pb_body = jina_pb2.DataRequestProto()
                json_format.ParseDict(request, self._pb_body)
            elif isinstance(request, str):
                self._pb_body = jina_pb2.DataRequestProto()
                json_format.Parse(request, self._pb_body)
            elif isinstance(request, bytes):
                self.buffer = request
            elif request is not None:
                # note ``None`` is not considered as a bad type
                raise ValueError(f'{typename(request)} is not recognizable')
            else:
                self._pb_body = jina_pb2.DataRequestProto()
                self._pb_body.header.request_id = random_identity()
        except Exception as ex:
            raise BadRequestType(
                f'fail to construct a {self.__class__} object from {request}'
            ) from ex

    @property
    def is_decompressed(self) -> bool:
        """
        Checks if the underlying proto object was already deserialized

        :return: True if the proto was deserialized before
        """
        return self.buffer is None

    @property
    def proto(self) -> 'jina_pb2.DataRequestProto':
        """
        Cast ``self`` to a :class:`jina_pb2.DataRequestProto`. Laziness will be broken and serialization will be recomputed when calling
        :meth:`SerializeToString`.
        :return: protobuf instance
        """
        if not self.is_decompressed:
            self._decompress()
        return self._pb_body

    def _decompress(self):
        self._pb_body = jina_pb2.DataRequestProto()
        self._pb_body.ParseFromString(self.buffer)
        self.buffer = None

    def to_dict(self) -> Dict:
        """Return the object in Python dictionary.

        .. note::
            Array like object such as :class:`numpy.ndarray` (i.e. anything described as :class:`jina_pb2.NdArrayProto`)
            will be converted to Python list.

        :return: dict representation of the object
        """
        da = self.docs
        self.proto.data.docs.CopyFrom(DocumentArray().to_protobuf())
        from google.protobuf.json_format import MessageToDict

        d = MessageToDict(
            self.proto, preserving_proto_field_name=True, use_integers_for_enums=True
        )
        d['data'] = da.to_dict()
        return d

    @property
    def docs(self) -> 'DocumentArray':
        """Get the :class: `DocumentArray` with sequence `data.docs` as content.

        .. # noqa: DAR201"""
        return self.data.docs

    @cached_property
    def data(self) -> 'DataRequest._DataContent':
        """Get the data contaned in this data request

        :return: the data content as an instance of _DataContent wrapping docs
        """
        return DataRequest._DataContent(self.proto.data)

    @property
    def parameters(self) -> Dict:
        """Return the `parameters` field of this DataRequest as a Python dict
        :return: a Python dict view of the parameters.
        """
        # if u get this u need to have it decompressed
        return json_format.MessageToDict(self.proto.parameters)

    @parameters.setter
    def parameters(self, value: Dict):
        """Set the `parameters` field of this Request to a Python dict
        :param value: a Python dict
        """
        self.proto.parameters.Clear()
        self.proto.parameters.update(value)

    @property
    def response(self):
        """
        Returns the response of this request.

        :return: the response of this request (self) as an instance of Response
        """
        return Response(request=self.proto)

    @property
    def status(self):
        """
        Returns the status from the header field

        :return: the status object of this request
        """
        return self.proto.header.status

    @classmethod
    def from_proto(cls, request: 'jina_pb2.DataRequestProto'):
        """Creates a new DataRequest object from a given :class:`DataRequestProto` object.
        :param request: the to-be-copied data request
        :return: the new message object
        """
        return cls(request=request)

    def __copy__(self):
        return DataRequest(request=self.proto)

    def __deepcopy__(self, _):
        return DataRequest(request=copy.deepcopy(self.proto))


class Response(DataRequest):
    """
    Response is the :class:`Request` object returns from the flow. Right now it shares the same representation as
    :class:`Request`. At 0.8.12, :class:`Response` is a simple alias. But it does give a more consistent semantic on
    the client API: send a :class:`Request` and receive a :class:`Response`.

    .. note::
        For now it only exposes `Docs` and `GroundTruth`. Users should very rarely access `Control` commands, so preferably
        not confuse the user by adding `CommandMixin`.
    """
