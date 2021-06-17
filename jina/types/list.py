from collections.abc import MutableSequence
from typing import Union

from google.protobuf import struct_pb2

from .mixin import ProtoTypeMixin


class ListView(ProtoTypeMixin, MutableSequence):
    """Create a Python mutable sequence view of Protobuf ListValue struct.

    This can be used in all Jina types where a protobuf.ListValue is returned.

    Used inside `StructView` when the inner element is a `ListValue`
    """

    def __init__(self, list: struct_pb2.ListValue):
        """Create a Python list view of Protobuf ListValue.

        :param list: the protobuf ListValue object
        """
        self._pb_body = list

    def insert(self, index: int, object) -> None:
        """
        Insert any proto object into the list

        :param index: Position of the insertion.
        :param object: The object that needs to be inserted.
        """
        self._pb_body.insert(index, object)

    def __getitem__(self, i: Union[int, slice]):
        if i < len(self):
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

    def clear(self):
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR103
        """
        self._pb_body.Clear()
