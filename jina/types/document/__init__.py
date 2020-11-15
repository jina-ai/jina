from typing import Union, Dict, Iterator

from google.protobuf import json_format

from .uid import *
from ... import NdArray
from ...helper import cached_property
from ...proto import jina_pb2

if False:
    import numpy as np

_empty_doc = jina_pb2.DocumentProto()


class Document:
    def __init__(self, document: Union[bytes, Dict, 'jina_pb2.DocumentProto', None] = None,
                 copy: bool = False):
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

    def __getattr__(self, name: str):
        # https://docs.python.org/3/reference/datamodel.html#object.__getattr__
        if hasattr(_empty_doc, name):
            return getattr(self._document, name)
        else:
            raise AttributeError

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
