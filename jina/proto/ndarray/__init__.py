from typing import TypeVar

AnyNdArray = TypeVar('AnyNdArray')

if False:
    from .. import jina_pb2


class BaseNdArray:
    """A base class for containing the protobuf message of NdArray. It defines interfaces
    for easier get/set value.

    Do not use this class directly. Subclass should be used.
    """

    def __init__(self, proto: 'jina_pb2._reflection.GeneratedProtocolMessageType' = None, *args, **kwargs):
        """

        :param proto: the protobuf message, when not given then create a new one via :meth:`get_null_proto`
        """
        if proto:
            self.proto = proto  # a weak ref/copy
        else:
            self.proto = self.null_proto()

        self.is_sparse = False  # set to true if the ndarray is sparse

    @property
    def null_proto(self) -> 'jina_pb2._reflection.GeneratedProtocolMessageType':
        """Get the new protobuf representation"""
        raise NotImplementedError

    @property
    def value(self) -> AnyNdArray:
        """Return the value of the ndarray, in numpy, scipy, tensorflow, pytorch type"""
        raise NotImplementedError

    @value.setter
    def value(self, value: AnyNdArray):
        """Set the value from numpy, scipy, tensorflow, pytorch type to protobuf"""
        raise NotImplementedError

    def copy_to(self, proto: 'jina_pb2._reflection.GeneratedProtocolMessageType') -> 'BaseNdArray':
        """Copy itself to another protobuf message, return a view of the copied message"""
        proto.CopyFrom(self.proto)
        return BaseNdArray(proto)
