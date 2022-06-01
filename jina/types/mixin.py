from typing import Dict

from jina.helper import TYPE_CHECKING, T, deprecate_by, typename

if TYPE_CHECKING:
    from jina.proto import jina_pb2


class ProtoTypeMixin:
    """The base mixin class of all Jina types.

    .. note::
        - All Jina types should inherit from this class.
        - All subclass should have ``self._pb_body``
        - All subclass should implement ``__init__`` with the possibility of initializing from ``None``, e.g.:

            .. highlight:: python
            .. code-block:: python

                class MyJinaType(ProtoTypeMixin):
                    def __init__(self, proto: Optional[jina_pb2.SomePbMsg] = None):
                        self._pb_body = proto or jina_pb2.SomePbMsg()

    """

    def to_json(self) -> str:
        """Return the object in JSON string

        :return: JSON string of the object
        """
        from google.protobuf.json_format import MessageToJson

        return MessageToJson(
            self.proto, preserving_proto_field_name=True, sort_keys=True
        )

    def to_dict(self, **kwargs) -> Dict:
        """Return the object in Python dictionary.

        .. note::
            Array like object such as :class:`numpy.ndarray` (i.e. anything described as :class:`jina_pb2.NdArrayProto`)
            will be converted to Python list.

        :param kwargs: Extra kwargs to be passed to MessageToDict, like use_integers_for_enums

        :return: dict representation of the object
        """
        from google.protobuf.json_format import MessageToDict

        return MessageToDict(self.proto, preserving_proto_field_name=True, **kwargs)

    @property
    def proto(self) -> 'jina_pb2._reflection.GeneratedProtocolMessageType':
        """Return the underlying Protobuf object

        :return: Protobuf representation of the object
        """
        return self._pb_body

    def to_bytes(self) -> bytes:
        """Return the serialized the message to a string.

        For more Pythonic code, please use ``bytes(...)``.

        :return: binary string representation of the object
        """
        return self.proto.SerializePartialToString()

    def __getstate__(self):
        return self._pb_body.__getstate__()

    def __setstate__(self, state):
        self.__init__()
        self._pb_body.__setstate__(state)

    @property
    def nbytes(self) -> int:
        """Return total bytes consumed by protobuf.

        :return: number of bytes
        """
        return len(bytes(self))

    def __getattr__(self, name: str):
        return getattr(self._pb_body, name)

    def __repr__(self):
        content = str(tuple(field[0].name for field in self.proto.ListFields()))
        content += f' at {id(self)}'
        return f'<{typename(self)} {content.strip()}>'

    def MergeFrom(self: T, other: T) -> None:
        """Merge the content of target

        :param other: the document to merge from
        """
        self._pb_body.MergeFrom(other._pb_body)

    def CopyFrom(self: T, other: T) -> None:
        """Copy the content of target

        :param other: the document to copy from
        """
        self._pb_body.CopyFrom(other._pb_body)

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
        if other is None:
            return False
        return self.proto == other.proto

    def __bytes__(self):
        return self.to_bytes()

    dict = deprecate_by(to_dict)
    json = deprecate_by(to_json)
    binary_str = deprecate_by(to_bytes)
