import pprint
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
        return MessageToJson(self._pb_body)

    def dict(self) -> Dict:
        """Return the object in Python dictionary

        :return: dict representation of the object
        """
        return MessageToDict(self._pb_body)

    @property
    def proto(self) -> 'jina_pb2._reflection.GeneratedProtocolMessageType':
        """Return the underlying Protobuf object

        :return: Protobuf representation of the object
        """
        return self._pb_body

    @property
    def binary_str(self) -> bytes:
        """Return the serialized the message to a string.

        :return: binary string representation of the object
        """
        return self._pb_body.SerializeToString()

    def __getattr__(self, name: str):
        return getattr(self._pb_body, name)

    def __str__(self):
        return str(self._build_content_dict())

    def __repr__(self):
        content = ' '.join(f'{k}={v}' for k, v in self._build_content_dict().items())
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
