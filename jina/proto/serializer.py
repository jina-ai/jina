from .. import Request


class RequestProto:
    """This class is a drop-in replacement for gRPC default serializer.

    It replace default serializer to make sure we always work with `Request`

    """

    @staticmethod
    def SerializeToString(x: 'Request'):
        return x.as_pb_object.SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        return Request(x)
