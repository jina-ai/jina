from .jina_pb2 import RequestProto as rp
from .. import Request


class RequestProto:
    """This class is a dropin replacement for gRPC default serializer.

    It replace default serializer to make sure we always work with `Request`

    """

    @staticmethod
    def SerializeToString(x: 'Request'):
        return x.as_pb_object.SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        return Request(rp.FromString(x))
