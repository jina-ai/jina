from collections.abc import MutableSequence
from typing import Union, List, Any

from google.protobuf import struct_pb2

from ..base import BaseProtoView


class ListView(BaseProtoView, MutableSequence):
    """Create a Python mutable sequence view of Protobuf ListValue struct.

    This can be used in all Jina types where a protobuf.ListValue is returned.

    Used inside `StructView` when the inner element is a `ListValue`
    """

    _PbMsg = struct_pb2.ListValue

    def insert(self, index: int, object: Any) -> None:
        """
        Insert any value that can be converted into a struct_pb2.Value into the list

        :param index: Position of the insertion.
        :param object: The object that needs to be inserted.
        """
        if index >= len(self):
            self._pb_body.append(object)
        else:
            self[index] = object

    def __getitem__(self, i: Union[int, slice]):
        if isinstance(i, int) and i >= len(self):
            raise IndexError('list index out of range')
        value = self._pb_body[i]
        if isinstance(value, struct_pb2.Struct):
            from .struct import StructView

            return StructView(value)
        elif isinstance(value, struct_pb2.ListValue):
            return ListView(value)
        else:
            return value

    def __setitem__(self, i, value):
        self._pb_body[i] = value

    def __delitem__(self, i: Union[int, slice]) -> None:
        del self._pb_body[i]

    def __len__(self) -> int:
        return len(self._pb_body)

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __eq__(self, other: Union['ListView', List]):
        if isinstance(other, List):
            return list(self) == other
        elif isinstance(other, ListView):
            return self.proto == other.proto
        else:
            return False

    def __contains__(self, object: Any):
        for element in self:
            if element == object:
                return True

        return False
