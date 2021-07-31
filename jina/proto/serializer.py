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
