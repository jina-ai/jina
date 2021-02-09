from .. import Request


class RequestProto:
    """This class is a drop-in replacement for gRPC default serializer.

    It replaces default serializer to make sure we always work with `Request`.
    """

    @staticmethod
    def SerializeToString(x: 'Request'):
        """
        Serialize the `:class:`Request` and returns it as a string.

        :param x: Object with Jina primitive data type `:class:`Request`.
        :return: String of the serialized `:class:`Request` instance.
        """
        return x.proto.SerializeToString()

    @staticmethod
    def FromString(x: bytes):
        """
        Return a new `:class:`Request` type instance deserialized from the given bytes data.

        :param x: Serialized bytes data.
        :return: `:class:`Request` type instance.
        """
        return Request(x)
