from functools import lru_cache

from . import jina_pb2
from ..types.message import Message
from ..types.request import Request


class RequestProto:
    """This class is a drop-in replacement for gRPC default serializer.

    It replace default serializer to make sure we always work with `Request`

    """

    @staticmethod
    def SerializeToString(x: 'Request'):
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
        return Request(x)


class MessageProto:
    """This class is a drop-in replacement for gRPC default serializer.
    It replace default serializer to make sure we always work with `Message`
    """

    @staticmethod
    @lru_cache()
    def SerializeToString(x: 'Message'):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        return x.proto.SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        """
        mp = jina_pb2.MessageProto()
        mp.ParseFromString(x)
        return Message.from_proto(mp)
