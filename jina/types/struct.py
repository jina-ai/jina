from collections.abc import MutableMapping

from google.protobuf.struct_pb2 import Struct


class StructView(MutableMapping):
    """Create a Python mutable mapping view of Protobuf Struct.

    This can be used in all Jina types where a protobuf.Struct is returned, e.g. Document.tags
    """

    def __init__(self, struct: Struct):
        """Create a Python dict view of Protobuf Struct.

        :param struct: the protobuf Struct object
        """
        self._pb_body = struct

    def __setitem__(self, key, value):
        self._pb_body[key] = value

    def __delitem__(self, key):
        del self._pb_body[key]

    def __getitem__(self, key):
        return self._pb_body[key]

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
