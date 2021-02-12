import pprint
from typing import Dict

from google.protobuf.json_format import MessageToJson, MessageToDict

from ..helper import typename
from ..proto import jina_pb2


class ProtoTypeMixin:
    def json(self) -> str:
        """Return the object in JSON string """
        return MessageToJson(self._pb_body)

    def dict(self) -> Dict:
        """Return the object in Python dictionary """
        return MessageToDict(self._pb_body)

    @property
    def proto(self) -> jina_pb2._reflection.GeneratedProtocolMessageType:
        """Return the underlying Protobuf object """
        return self._pb_body

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
        """Helper method for __str__ and __repr__ """
        content = self.dict()
        if hasattr(self, '_attributes_in_str') and isinstance(self._attributes_in_str, list):
            content = {k: content[k] for k in self._attributes_in_str}
        return content
