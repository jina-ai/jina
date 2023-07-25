import os
from typing import Iterable, List, Union

from jina.proto import jina_pb2
from jina.types.request.data import DataRequest


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
    It replaces default serializer to make sure the message sending interface is convenient.
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
            protos.append(x.proto_with_data)
        else:
            protos = [r.proto_with_data for r in x]

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
        return [DataRequest.from_proto(request) for request in rlp.requests]


class EndpointsProto:
    """Since the serializer is replacing the `jina_pb2 to know how to exactly serialize messages, this is just a placeholder that
    delegates the serializing and deserializing to the internal protobuf structure with no extra optimization.
    """

    @staticmethod
    def SerializeToString(x):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return x.SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        ep = jina_pb2.EndpointsProto()
        ep.ParseFromString(x)

        return ep


class StatusProto:
    """Since the serializer is replacing the `jina_pb2 to know how to exactly serialize messages, this is just a placeholder that
    delegates the serializing and deserializing to the internal protobuf structure with no extra optimization.
    """

    @staticmethod
    def SerializeToString(x):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return x.SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        sp = jina_pb2.StatusProto()
        sp.ParseFromString(x)

        return sp


class JinaInfoProto:
    """Since the serializer is replacing the `jina_pb2` to know how to exactly serialize messages, this is just a placeholder that
    delegates the serializing and deserializing to the internal protobuf structure with no extra optimization.
    """

    @staticmethod
    def SerializeToString(x):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return x.SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        ip = jina_pb2.JinaInfoProto()
        ip.ParseFromString(x)

        return ip


class SnapshotId:
    """Placeholder that delegates the serialization and deserialization to the internal protobuf"""

    @staticmethod
    def SerializeToString(x):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return x.SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        si = jina_pb2.SnapshotId()
        si.ParseFromString(x)

        return si


class SnapshotStatusProto:
    """Placeholder that delegates the serialization and deserialization to the internal protobuf"""

    @staticmethod
    def SerializeToString(x):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return x.SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        sp = jina_pb2.SnapshotStatusProto()
        sp.ParseFromString(x)

        return sp


class RestoreSnapshotCommand:
    """Placeholder that delegates the serialization and deserialization to the internal protobuf"""

    @staticmethod
    def SerializeToString(x):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return x.SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        rpcommand = jina_pb2.RestoreSnapshotCommand()
        rpcommand.ParseFromString(x)

        return rpcommand


class RestoreId:
    """Placeholder that delegates the serialization and deserialization to the internal protobuf"""

    @staticmethod
    def SerializeToString(x):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return x.SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        ri = jina_pb2.RestoreId()
        ri.ParseFromString(x)

        return ri


class RestoreSnapshotStatusProto:
    """Placeholder that delegates the serialization and deserialization to the internal protobuf"""

    @staticmethod
    def SerializeToString(x):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return x.SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        rsp = jina_pb2.RestoreSnapshotStatusProto()
        rsp.ParseFromString(x)

        return rsp


class SingleDocumentRequestProto:
    """Placeholder that delegates the serialization and deserialization to the internal protobuf"""

    @staticmethod
    def SerializeToString(x):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return x.SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        rsp = jina_pb2.SingleDocumentRequestProto()
        rsp.ParseFromString(x)

        return rsp
