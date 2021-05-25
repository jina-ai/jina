from google.protobuf.internal.well_known_types import Struct
from google.protobuf.json_format import MessageToDict


class StructView(dict):
    """Create a Python dict view of Protobuf Struct.

    This can be used in all Jina types where a protobuf.Struct is returned, e.g. Document.tags

    """

    def __init__(self, struct: Struct):
        """Create a Python dict view of Protobuf Struct.

        :param struct: the protobuf Struct object
        """
        super().__init__(MessageToDict(struct))
        self._pb_body = struct

    def __setitem__(self, key, value):
        self._pb_body[key] = value

    def __delitem__(self, key):
        del self._pb_body[key]

    def update(self, dictionary):  # pylint: disable=invalid-name
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR103
        """
        self._pb_body.update(dictionary)

    def clear(self) -> None:
        """
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR103
        """
        self._pb_body.Clear()
