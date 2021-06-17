from collections.abc import MutableMapping

from google.protobuf import struct_pb2

from .mixin import ProtoTypeMixin


class StructView(ProtoTypeMixin, MutableMapping):
    """Create a Python mutable mapping view of Protobuf Struct.

    This can be used in all Jina types where a protobuf.Struct is returned, e.g. Document.tags
    """

    def __init__(self, struct: struct_pb2.Struct):
        """Create a Python dict view of Protobuf Struct.

        :param struct: the protobuf Struct object
        """
        self._pb_body = struct

    def __setitem__(self, key, value):
        self._pb_body[key] = value

    def __delitem__(self, key):
        del self._pb_body[key]

    def __getitem__(self, key):
        if key in self._pb_body.keys():
            value = self._pb_body[key]
            # TODO: Maybe do the same with ListValue and build a ListValueView
            if isinstance(value, struct_pb2.Struct):
                return StructView(value)
            else:
                return value
        else:
            raise KeyError()

    def __len__(self) -> int:
        return len(self._pb_body.keys())

    def __iter__(self):
        for key in self._pb_body.keys():
            yield key

    def update(self, d, **kwargs):  # pylint: disable=invalid-name
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR103
        """
        self._pb_body.update(d)

    def clear(self) -> None:
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR103
        """
        self._pb_body.Clear()
