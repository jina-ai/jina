import os
import urllib.parse
from typing import Union, Dict, Iterator

from google.protobuf import json_format

from .uid import *
from ... import NdArray
from ...drivers.helper import guess_mime
from ...helper import cached_property, is_url
from ...proto import jina_pb2

if False:
    import numpy as np

_empty_doc = jina_pb2.DocumentProto()
_buffer_sniff = False


class Document:
    def __init__(self, document: Union[bytes, Dict, 'jina_pb2.DocumentProto', None] = None,
                 mime_type: str = None,
                 copy: bool = False, **kwargs):
        self._document = jina_pb2.DocumentProto()
        if isinstance(document, jina_pb2.DocumentProto):
            if copy:
                self._document.CopyFrom(document)
            else:
                self._document = document
        elif isinstance(document, dict):
            json_format.ParseDict(document, self._document)
        elif isinstance(document, str):
            json_format.Parse(document, self._document)
        elif isinstance(document, bytes):
            self._document.ParseFromString(document)

        if mime_type:
            self._document.mime_type = mime_type

        for k, v in kwargs.items():
            if hasattr(self._document, k):
                setattr(self._document, k, v)

    def __getattr__(self, name: str):
        if hasattr(_empty_doc, name):
            return getattr(self._document, name)
        else:
            raise AttributeError

    def update_id(self):
        self._document.id = uid.new_doc_id(self._document)

    @property
    def blob(self) -> 'np.ndarray':
        return NdArray(self._document.blob).value

    @blob.setter
    def blob(self, value: 'np.ndarray'):
        NdArray(self._document.blob).value = value

    @property
    def embedding(self) -> 'np.ndarray':
        return NdArray(self._document.blob).value

    @embedding.setter
    def embedding(self, value: 'np.ndarray'):
        NdArray(self._document.blob).value = value

    @property
    def matches(self) -> Iterator['Document']:
        for d in self._document.matches:
            yield Document(d)

    @property
    def chunks(self) -> Iterator['Document']:
        for d in self._document.chunks:
            yield Document(d)

    def add_match(self, doc_id: str, score_value: float, **kwargs) -> 'Document':
        r = self._document.matches.add()
        r.id = doc_id
        r.granularity = self._document.granularity
        r.adjacency = self._document.adjacency + 1
        r.score.ref_id = self._document.id
        r.score.value = score_value
        for k, v in kwargs.items():
            if hasattr(r.score, k):
                setattr(r.score, k, v)
        return Document(r)

    def add_chunk(self) -> 'Document':
        c = self._document.chunks.add()
        c.parent_id = self._document.id
        c.granularity = self._document.granularity + 1
        if not c.mime_type:
            c.mime_type = self._document.mime_type
        c.id = uid.new_doc_id(c)
        return Document(c)

    @cached_property
    def as_pb_object(self) -> 'jina_pb2.DocumentProto':
        return self._document

    @property
    def buffer(self) -> bytes:
        return self._document.buffer

    @buffer.setter
    def buffer(self, value: bytes):
        self._document.buffer = value
        if not self._document.mime_type and _buffer_sniff:
            try:
                import magic
                self._document.mime_type = magic.from_buffer(value, mime=True)
            except Exception as ex:
                default_logger.warning(f'can not sniff the MIME type: {repr(ex)}')

    @property
    def uri(self) -> str:
        return self._document.uri

    @uri.setter
    def uri(self, value: str):
        scheme = urllib.parse.urlparse(value).scheme
        if ((scheme in {'http', 'https'} and is_url(value))
                or (scheme in {'data'})
                or os.path.exists(value)
                or os.access(os.path.dirname(value), os.W_OK)):
            self._document.uri = value
            self._document.mime_type = guess_mime(value)
        else:
            raise ValueError(f'{value} is not a valid URI')
