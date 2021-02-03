from typing import TypeVar, Union

from ..mixin import ProtoTypeMixin
from ...proto import jina_pb2

PbMessageType = jina_pb2._reflection.GeneratedProtocolMessageType

AnyNdArray = TypeVar('AnyNdArray')

__all__ = ['BaseNdArray']


class BaseNdArray(ProtoTypeMixin):
    """A base class for containing the protobuf message of NdArray. It defines interfaces
    for easier get/set value.

    Do not use this class directly. Subclass should be used.
    """

    def __init__(self, proto: Union['PbMessageType', AnyNdArray] = None,
                 *args, **kwargs):
        """

        :param proto: the protobuf message, when not given then create a new one via :meth:`get_null_proto`
        """
        if proto is not None and isinstance(type(proto), PbMessageType):
            self._pb_body = proto  # a weak ref/copy
        else:
            self._pb_body = self.null_proto()
            if proto is not None:
                # casting using the subclass :attr:`value` interface
                self.value = proto

    @property
    def null_proto(self) -> 'PbMessageType':
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

    def copy_to(self, proto: 'PbMessageType') -> 'BaseNdArray':
        """Copy itself to another protobuf message, return a view of the copied message"""
        proto.CopyFrom(self._pb_body)
        return self.__class__(proto)
