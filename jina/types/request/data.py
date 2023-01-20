import copy
from typing import Dict, Optional, Type, TypeVar, Union

from docarray.documents.legacy import DocumentArray
from google.protobuf import json_format

from jina.excepts import BadRequestType
from jina.helper import cached_property, random_identity, typename
from jina.proto import jina_pb2
from jina.types.request import Request

RequestSourceType = TypeVar(
    'RequestSourceType', jina_pb2.DataRequestProto, str, Dict, bytes
)


class DataRequest(Request):
    """
    Represents a DataRequest used for exchanging :class:`docarray.DocumentArray` with and within a Flow.

    When calling :meth:`~jina.clients.mixin.PostMixin.post` on any Jina client,
    the provided input :class:`docarray.DocumentArray` will be
    converted to a :class:`DataRequest` before being sent to a Flow.
    """

    class _DataContent:
        def __init__(
            self,
            content: 'jina_pb2.DataRequestProto.DataContentProto',
            document_array_cls: Type[DocumentArray],
        ):
            self._content = content
            self._loaded_doc_array = None
            self.document_array_cls = document_array_cls

        @property
        def docs(self) -> 'DocumentArray':
            """Get the :class: `DocumentArray` with sequence `data.docs` as content.

            .. # noqa: DAR201"""
            if not self._loaded_doc_array:
                if self._content.WhichOneof('documents') == 'docs_bytes':
                    self._loaded_doc_array = self.document_array_cls.from_bytes(
                        self._content.docs_bytes
                    )
                else:
                    self._loaded_doc_array = self.document_array_cls.from_protobuf(
                        self._content.docs
                    )

            return self._loaded_doc_array

        @docs.setter
        def docs(self, value: DocumentArray):
            """Override the DocumentArray with the provided one

            :param value: a DocumentArray
            """
            self.set_docs_convert_arrays(value)

        def set_docs_convert_arrays(self, value: DocumentArray):
            """ " Convert embedding and tensor to given type, then set DocumentArray

            :param value: a DocumentArray
            """
            if value is not None:
                self._loaded_doc_array = None
                self._content.docs.CopyFrom(value.to_protobuf())

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
        self._pb_body = None
        self.document_array_cls = DocumentArray

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
        Checks if the underlying proto object was already deserialized into a :class:`jina.proto.jina_pb2.DataRequestProto` or
        :class:`jina.proto.jina_pb2.DataRequestProtoWoData`. This does not necessarily mean that the data (docs) inside the request is also decompressed.
           :return: True if the proto was deserialized before
        """
        return type(self._pb_body) in [
            jina_pb2.DataRequestProto,
            jina_pb2.DataRequestProtoWoData,
        ]

    @property
    def is_decompressed_with_data(self) -> bool:
        """
        Checks if the underlying proto object was already deserialized into a :class:`jina.proto.jina_pb2.DataRequestProto`. In this case the full proto is decompressed, including the data (docs).
           :return: True if the proto was deserialized before, including the data (docs)
        """
        return type(self._pb_body) is jina_pb2.DataRequestProto

    @property
    def is_decompressed_wo_data(self) -> bool:
        """
        Checks if the underlying proto object was already deserialized into a :class:`jina.proto.jina_pb2.DataRequestProtoWoData`. It means that the proto is loaded without the data ( docs ).

        :return: True if the proto was deserialized before into a DataRequest without docs
        """
        return type(self._pb_body) is jina_pb2.DataRequestProtoWoData

    @property
    def proto_wo_data(
        self,
    ) -> Union['jina_pb2.DataRequestProtoWoData', 'jina_pb2.DataRequestProto']:
        """
        Transform the current buffer to a :class:`jina_pb2.DataRequestProtoWoData` unless the full proto has already
        been initialized or . Laziness will be broken and serialization will be recomputed when
        calling :meth:`SerializeToString`.
        :return: protobuf instance containing parameters
        """
        if self._pb_body is None:
            self._decompress_wo_data()
        return self._pb_body

    @property
    def proto(
        self,
    ) -> Union['jina_pb2.DataRequestProto', 'jina_pb2.DataRequestProtoWoData']:
        """
        Cast ``self`` to a :class:`jina_pb2.DataRequestProto` or a :class:`jina_pb2.DataRequestProto`. Laziness will be broken and serialization will be recomputed when calling.
        it returns the underlying proto if it already exists (even if he is loaded without data) or creates a new one.
        :meth:`SerializeToString`.
        :return: DataRequestProto protobuf instance
        """
        if not self.is_decompressed:
            self._decompress()
        return self._pb_body

    @property
    def proto_with_data(
        self,
    ) -> 'jina_pb2.DataRequestProto':
        """
        Cast ``self`` to a :class:`jina_pb2.DataRequestProto`. Laziness will be broken and serialization will be recomputed when calling.
        :meth:`SerializeToString`.
        :return: DataRequestProto protobuf instance
        """
        if not self.is_decompressed_with_data:
            self._decompress()
        return self._pb_body

    def _decompress_wo_data(self):
        """Decompress the buffer into a DataRequestProto without docs, it is useful if one want to access the parameters
        or the header of the proto without the cost of deserializing the Docs."""

        # Under the hood it used a different DataRequestProto (the DataRequestProtoWoData) that will just ignore the
        # bytes from the bytes related to the docs that are store at the end of the Proto buffer
        self._pb_body = jina_pb2.DataRequestProtoWoData()
        self._pb_body.ParseFromString(self.buffer)
        self.buffer = None

    def _decompress(self):
        """Decompress the buffer into a DataRequestProto"""
        if self.buffer:
            self._pb_body = jina_pb2.DataRequestProto()
            self._pb_body.ParseFromString(self.buffer)
            self.buffer = None
        elif self.is_decompressed_wo_data:
            self._pb_body_old = self._pb_body
            self._pb_body = jina_pb2.DataRequestProto()
            self._pb_body.ParseFromString(self._pb_body_old.SerializePartialToString())
            del self._pb_body_old
        else:
            raise ValueError('the buffer is already decompressed')

    def to_dict(self) -> Dict:
        """Return the object in Python dictionary.

        .. note::
            Array like object such as :class:`numpy.ndarray` (i.e. anything described as :class:`jina_pb2.NdArrayProto`)
            will be converted to Python list.

        :return: dict representation of the object
        """
        da = self.docs
        from google.protobuf.json_format import MessageToDict

        d = MessageToDict(
            self.proto_wo_data,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
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
        """Get the data contained in this data request

        :return: the data content as an instance of _DataContent wrapping docs
        """
        return DataRequest._DataContent(
            self.proto_with_data.data, document_array_cls=self.document_array_cls
        )

    @property
    def parameters(self) -> Dict:
        """Return the `parameters` field of this DataRequest as a Python dict

        :return: a Python dict view of the parameters.
        """
        # if u get this u need to have it decompressed
        return json_format.MessageToDict(self.proto_wo_data.parameters)

    @parameters.setter
    def parameters(self, value: Dict):
        """Set the `parameters` field of this Request to a Python dict

        :param value: a Python dict
        """
        self.proto_wo_data.parameters.Clear()
        self.proto_wo_data.parameters.update(value)

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
        return self.proto_wo_data.header.status

    @property
    def last_executor(self):
        """
        Returns the name of the last Executor that has processed this Request

        :return: the name of the last Executor that processed this Request
        """
        if len(self.proto_wo_data.routes) > 0:
            return self.proto_wo_data.routes[-1].executor

    def add_executor(self, executor_name: str):
        """
        Adds Executor the the request routes

        :param executor_name: name of the Executor processing the Request to be added to the routes
        """
        route_proto = jina_pb2.RouteProto()
        route_proto.executor = executor_name
        self.proto_wo_data.routes.append(route_proto)

    @property
    def routes(self):
        """
        Returns the routes from the request

        :return: the routes object of this request
        """
        return self.proto_wo_data.routes

    @property
    def request_id(self):
        """
        Returns the request_id from the header field

        :return: the request_id object of this request
        """
        return self.proto.header.request_id

    @classmethod
    def from_proto(cls, request: 'jina_pb2.DataRequestProto'):
        """Creates a new DataRequest object from a given :class:`DataRequestProto` object.
        :param request: the to-be-copied data request
        :return: the new message object
        """
        return cls(request=request)

    def __copy__(self):
        return DataRequest(request=self.proto_with_data)

    def __deepcopy__(self, _):
        return DataRequest(request=copy.deepcopy(self.proto_with_data))


class Response(DataRequest):
    """
    Response is the :class:`~jina.types.request.Request` object returned by the flow.

    At the moment it is an alias for :class:`~jina.types.request.Request`,
    and therefore shares an identical representation.
    Currently, its sole purpose is to give a more consistent semantic on
    the client API: send a :class:`~jina.types.request.data.DataRequest` and receive a :class:`~jina.types.request.data.Response`.
    """
