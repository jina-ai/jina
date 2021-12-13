from collections.abc import MutableMapping
from typing import Union, Dict

from google.protobuf import struct_pb2

from ..base import BaseProtoView


class StructView(BaseProtoView, MutableMapping):
    """Create a Python mutable mapping view of Protobuf Struct.

    This can be used in all Jina types where a protobuf.Struct is returned, e.g. Document.tags

    .. note::
        This class behaves like :class:`defaultdict`.
    """

    _PbMsg = struct_pb2.Struct

    def __setitem__(self, key, value):
        self._pb_body[key] = value

    def __delitem__(self, key):
        del self._pb_body[key]

    def __getitem__(self, key):
        if key in self._pb_body:
            value = self._pb_body[key]
            if isinstance(value, struct_pb2.Struct):
                return StructView(value)
            elif isinstance(value, struct_pb2.ListValue):
                from .list import ListView

                return ListView(value)
            else:
                return value
        else:
            self._pb_body[key] = {}
            return StructView(self._pb_body[key])

    def __contains__(self, item):
        return item in self._pb_body

    def __len__(self) -> int:
        return len(self._pb_body.keys())

    def __iter__(self):
        for key in self._pb_body.keys():
            yield key

    def __eq__(self, other: Union['StructView', Dict]):
        if isinstance(other, dict):
            return self.to_dict() == other
        elif isinstance(other, StructView):
            return self.proto == other.proto
        else:
            return False

    def update(
        self, d: Union['StructView', struct_pb2.Struct], **kwargs
    ):  # pylint: disable=invalid-name
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR103
        """
        if isinstance(d, StructView):
            self._pb_body.update(d._pb_body)
        else:
            self._pb_body.update(d)
