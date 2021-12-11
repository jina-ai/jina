from typing import Dict, Tuple, Union, Optional, TYPE_CHECKING, Type, List

from .helper import typename, T, deprecate_by

if TYPE_CHECKING:
    from google.protobuf.message import Message


class BaseProtoView:
    """The base mixin class of all Jina types.

    .. note::
        - All Jina types should inherit from this class.
        - All subclass should have ``self._pb_body``
        - All subclass should implement ``__init__`` with the possibility of initializing from ``None``, e.g.:

            .. highlight:: python
            .. code-block:: python

                class MyJinaType(ProtoTypeMixin):

                    def __init__(self, proto: Optional[docarray_pb2.SomePbMsg] = None):
                        self._pb_body = proto or docarray_pb2.SomePbMsg()

    """

    _PbMsg: Type['Message'] = None

    def __init__(
        self,
        obj: Optional[Union[bytes, 'BaseProtoView', 'Message']] = None,
        copy: bool = False,
    ):
        self._pb_body = None

        if isinstance(obj, BaseProtoView):
            if copy:
                self._pb_body = self._PbMsg()
                self.CopyFrom(obj)
            else:
                self._pb_body = obj._pb_body
        elif isinstance(obj, self._PbMsg):
            if copy:
                self._pb_body = self._PbMsg()
                self._pb_body.CopyFrom(obj)
            else:
                self._pb_body = obj
        elif isinstance(obj, bytes):
            self._pb_body = self._PbMsg()
            self._pb_body.ParseFromString(obj)
        elif obj is None:
            self._pb_body = self._PbMsg()

    def to_json(self) -> str:
        """Return the object in JSON string

        :return: JSON string of the object
        """
        from google.protobuf.json_format import MessageToJson

        return MessageToJson(
            self._pb_body, preserving_proto_field_name=True, sort_keys=True
        )

    def to_dict(self) -> Dict:
        """Return the object in Python dictionary.

        .. note::
            Array like object such as :class:`numpy.ndarray` (i.e. anything described as :class:`docarray_pb2.NdArrayProto`)
            will be converted to Python list.

        :return: dict representation of the object
        """
        from google.protobuf.json_format import MessageToDict

        return MessageToDict(
            self._pb_body,
            preserving_proto_field_name=True,
        )

    @property
    def proto(self):
        """Return the underlying Protobuf object

        :return: Protobuf representation of the object
        """
        return self._pb_body

    def to_bytes(self) -> bytes:
        """Return the serialized the message to a string.

        For more Pythonic code, please use ``bytes(...)``.

        :return: binary string representation of the object
        """
        return self._pb_body.SerializePartialToString()

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
        return self.proto == other.proto

    def __bytes__(self):
        return self.to_bytes()

    def __copy__(self):
        return type(self)(self)

    def __deepcopy__(self, memodict={}):
        return type(self)(self, copy=True)

    @classmethod
    def attributes(
        cls,
        include_proto_fields: bool = True,
        include_proto_fields_camelcase: bool = False,
        include_properties: bool = False,
    ) -> List[str]:
        """Return all attributes supported by the Document, which can be accessed by ``doc.attribute``

        :param include_proto_fields: if set, then include all protobuf fields
        :param include_proto_fields_camelcase: if set, then include all protobuf fields in CamelCase
        :param include_properties: if set, then include all properties defined for Document class
        :return: a list of attributes in string.
        """

        support_keys = []

        if include_proto_fields:
            support_keys = [
                k
                for k, v in vars(cls._PbMsg).items()
                if 'FieldProperty' == type(v).__name__
            ]
        if include_proto_fields_camelcase:
            from google.protobuf.descriptor import _ToCamelCase

            support_keys += [
                _ToCamelCase(k)
                for k, v in vars(cls._PbMsg).items()
                if 'FieldProperty' == type(v).__name__
            ]

        if include_properties:
            support_keys += [
                p for p in dir(cls) if isinstance(getattr(cls, p), property)
            ]
        return list(set(support_keys))

    dict = deprecate_by(to_dict)
    json = deprecate_by(to_json)
    binary_str = deprecate_by(to_bytes)
