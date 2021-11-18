from typing import Dict, Tuple

from google.protobuf.json_format import MessageToJson, MessageToDict

from ..helper import typename, T
from ..proto import jina_pb2


class ProtoTypeMixin:
    """Mixin class of `ProtoType`."""

    def json(self) -> str:
        """Return the object in JSON string

        :return: JSON string of the object
        """
        return MessageToJson(
            self._pb_body, preserving_proto_field_name=True, sort_keys=True
        )

    def dict(self) -> Dict:
        """Return the object in Python dictionary

        :return: dict representation of the object
        """

        # NOTE: PLEASE DO NOT ADD `including_default_value_fields`,
        # it makes the output very verbose!
        return MessageToDict(
            self._pb_body,
            preserving_proto_field_name=True,
        )

    @property
    def proto(self) -> 'jina_pb2._reflection.GeneratedProtocolMessageType':
        """Return the underlying Protobuf object

        :return: Protobuf representation of the object
        """
        return self._pb_body

    def binary_str(self) -> bytes:
        """Return the serialized the message to a string.

        :return: binary string representation of the object
        """
        return self._pb_body.SerializePartialToString()

    @property
    def nbytes(self) -> int:
        """Return total bytes consumed by protobuf.

        :return: number of bytes
        """
        return len(self.binary_str())

    def __getattr__(self, name: str):
        return getattr(self._pb_body, name)

    def __repr__(self):
        content = str(self.non_empty_fields)
        content += f' at {id(self)}'
        return f'<{typename(self)} {content.strip()}>'

    @property
    def non_empty_fields(self) -> Tuple[str, ...]:
        """Return the set fields of the current Protobuf message that are not empty

        :return: the tuple of non-empty fields
        """
        return tuple(field[0].name for field in self._pb_body.ListFields())

    def MergeFrom(self: T, other: T) -> None:
        """Merge the content of target

        :param other: the document to merge from
        """
        self._pb_body.MergeFrom(other._pb_body)

    def CopyFrom(self: T, other: T) -> None:
        """Copy the content of target

        :param other: the document to copy from
        """
        self._pb_body.MergeFrom(other._pb_body)

    def clear(self) -> None:
        """Remove all values from all fields of this Document."""
        self._pb_body.Clear()

    def pop(self, *fields) -> None:
        """Remove the values from the given fields of this Document.

        :param fields: field names
        """
        for k in fields:
            self._pb_body.ClearField(k)

    def __eq__(self, other):
        return self.proto == other.proto
