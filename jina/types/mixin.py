from typing import Dict

from google.protobuf.json_format import MessageToJson, MessageToDict

from ..helper import typename
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
        return self._pb_body.SerializeToString()

    @property
    def nbytes(self) -> int:
        """Return total bytes consumed by protobuf.

        :return: number of bytes
        """
        return len(self.binary_str())

    def __getattr__(self, name: str):
        return getattr(self._pb_body, name)

    def __str__(self):
        return str(self._build_content_dict())

    def __repr__(self):
        d = self._build_content_dict()
        if isinstance(d, list):
            content = ' '.join(f'{v}' for v in self._build_content_dict())
        else:
            content = ' '.join(
                f'{k}={v}' for k, v in self._build_content_dict().items()
            )
        content += f' at {id(self)}'
        content = content.strip()
        return f'<{typename(self)} {content}>'

    def _build_content_dict(self):
        """Helper method for __str__ and __repr__

        :return: the dict representation for the object
        """
        content = self.dict()
        if hasattr(self, '_attributes_in_str') and isinstance(
            self._attributes_in_str, list
        ):
            content = {k: content[k] for k in self._attributes_in_str}
        return content
