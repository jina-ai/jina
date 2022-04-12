import os
from typing import Iterable, List, Union

from jina.proto import jina_pb2
from jina.types.request.control import ControlRequest
from jina.types.request.data import DataRequest


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
        if not x.is_decompressed:
            r = x.buffer
        else:
            r = x.proto.SerializePartialToString()
        os.environ['JINA_GRPC_SEND_BYTES'] = str(
            len(r) + int(os.environ.get('JINA_GRPC_SEND_BYTES', 0))
        )
        return r

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        os.environ['JINA_GRPC_RECV_BYTES'] = str(
            len(x) + int(os.environ.get('JINA_GRPC_RECV_BYTES', 0))
        )
        return DataRequest(x)


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
