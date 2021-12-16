from typing import List, Union, Iterable

from . import jina_pb2
from ..types.request.control import ControlRequest
from ..types.request.data import DataRequest
from ..types.request.data_hack import DataRequestHac
from ..types.request.data_old import DataRequestOld


class ControlRequestProto:
    """This class is a drop-in replacement for gRPC default serializer.

    It replace default serializer to make sure we always work with `Request`

    """

    @staticmethod
    def SerializeToString(x: 'ControlRequest'):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return x.proto.SerializePartialToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        proto = jina_pb2.ControlRequestProto()
        proto.ParseFromString(x)

        return ControlRequest(request=proto)


class DataRequestProtoHac:
    """This class is a drop-in replacement for gRPC default serializer.

    It replace default serializer to make sure we always work with `Request`

    """

    @staticmethod
    def SerializeToString(x: 'DataRequest'):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        if x._buffer is not None:
            return x._buffer
        return x.proto.SerializePartialToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """

        return DataRequestHac(x)


class DataRequestProto:
    """This class is a drop-in replacement for gRPC default serializer.

    It replace default serializer to make sure we always work with `Request`

    """

    @staticmethod
    def SerializeToString(x: 'DataRequest'):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        if x.is_decompressed:
            print('serialize to bytes')
            x.proto.docs = x.docs.to_bytes()
        return x.proto.SerializePartialToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """

        proto = jina_pb2.DataRequestProto()
        proto.ParseFromString(x)

        print(f'deserialize {id(x[0])} ')

        return DataRequest(proto)


class DataRequestProtoOld:
    """This class is a drop-in replacement for gRPC default serializer.

    It replace default serializer to make sure we always work with `Request`

    """

    @staticmethod
    def SerializeToString(x: 'DataRequestOld'):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return x.proto.SerializePartialToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """

        proto = jina_pb2.DataRequestProtoOld()
        proto.ParseFromString(x)

        return DataRequestOld(proto)


class DataRequestListProto:
    """This class is a drop-in replacement for gRPC default serializer.
    It replace default serializer to make sure the message sending interface is convenient.
    It can handle sending single messages or a list of messages. It also returns a list of messages.
    Effectively this is hiding MessageListProto from the consumer
    """

    @staticmethod
    def SerializeToString(x: 'Union[List[DataRequest], DataRequest]'):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        protos = []
        if not isinstance(x, Iterable):
            protos.append(x.proto)
        else:
            for r in x:
                protos.append(r.proto)

        return jina_pb2.DataRequestListProto(requests=protos).SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        rlp = jina_pb2.DataRequestListProto()
        rlp.ParseFromString(x)
        requests = []
        for request in rlp.requests:
            requests.append(DataRequest.from_proto(request))

        return requests
