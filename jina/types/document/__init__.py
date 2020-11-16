import mimetypes
import os
import urllib.parse
from typing import Union, Dict, Iterator, Optional, TypeVar

import numpy as np
from google.protobuf import json_format

from .uid import *
from ... import NdArray
from ...helper import is_url, typename, guess_mime
from ...importer import ImportExtensions
from ...proto import jina_pb2

_empty_doc = jina_pb2.DocumentProto()
_buffer_sniff = False
with ImportExtensions(required=False,
                      pkg_name='python-magic',
                      help_text=f'can not sniff the MIME type '
                                f'MIME sniffing requires brew install '
                                f'libmagic (Mac)/ apt-get install libmagic1 (Linux)'):
    _buffer_sniff = True

__all__ = ['Document', 'DocumentContentType', 'DocumentSourceType']

DocumentContentType = TypeVar('DocumentContentType', bytes, str, np.ndarray, jina_pb2.NdArrayProto, NdArray)
DocumentSourceType = TypeVar('DocumentSourceType',
                             jina_pb2.DocumentProto, bytes, str, Dict)


class Document:
    """Document is a basic data type in Jina. It offers a Pythonic interface to allow users
    access and manipulate :class:`jina_pb2.DocumentProto` without working with Protobuf itself.


    """

    def __init__(self, document: Optional[DocumentSourceType] = None,
                 copy: bool = False, **kwargs):
        """

        :param document: the document to construct from. If ``bytes`` is given
                then deserialize a :class:`DocumentProto`; ``dict`` is given then
                parse a :class:`DocumentProto` from it; ``str`` is given, then consider
                it as a JSON string and parse a :class:`DocumentProto` from it; finally,
                one can also give `DocumentProto` directly, then depending on the ``copy``,
                it builds a view or a copy from it.
        :param copy: when ``document`` is given as a :class:`DocumentProto` object, build a
                view (i.e. weak reference) from it or a deep copy from it.
        :param kwargs: other parameters to be set
        """
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

        self.update(**kwargs)

    def __getattr__(self, name: str):
        if hasattr(_empty_doc, name):
            return getattr(self._document, name)
        else:
            raise AttributeError

    def update_id(self):
        self._document.id = new_doc_id(self._document)

    @property
    def id_in_hash(self) -> int:
        return id2hash(self._document.id)

    @property
    def id_in_bytes(self) -> bytes:
        return id2bytes(self._document.id)

    @property
    def id(self) -> bytes:
        return self._document.id

    @id.setter
    def id(self, value: str):
        pass

    @property
    def blob(self) -> 'np.ndarray':
        return NdArray(self._document.blob).value

    @blob.setter
    def blob(self, value: Union['np.ndarray', 'jina_pb2.NdArrayProto', 'NdArray']):
        self._update_ndarray('blob', value)

    @property
    def embedding(self) -> 'np.ndarray':
        return NdArray(self._document.embedding).value

    @embedding.setter
    def embedding(self, value: Union['np.ndarray', 'jina_pb2.NdArrayProto', 'NdArray']):
        self._update_ndarray('embedding', value)

    def _update_ndarray(self, k, v):
        if isinstance(v, jina_pb2.NdArrayProto):
            getattr(self._document, k).CopyFrom(v)
        elif isinstance(v, np.ndarray):
            NdArray(getattr(self._document, k)).value = v
        elif isinstance(v, NdArray):
            NdArray(getattr(self._document, k)).is_sparse = v.is_sparse
            NdArray(getattr(self._document, k)).value = v.value
        else:
            raise TypeError(f'{k} is in unsupported type {typename(v)}')

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

    def add_chunk(self, document: Optional['Document'] = None, **kwargs) -> 'Document':
        """Add a sub-document (i.e chunk) to the current Document

        :return: the newly added sub-document in :class:`Document` view
        """
        c = self._document.chunks.add()
        if document is not None:
            c.CopyFrom(document.as_pb_object)

        with Document(c) as chunk:
            chunk.update(parent_id=self._document.id,
                         granularity=self._document.granularity + 1,
                         **kwargs)
            chunk.mime_type = self._document.mime_type
            return chunk

    def update(self, **kwargs):
        """Bulk update Document fields with key-value specified in kwargs """
        for k, v in kwargs.items():
            if isinstance(v, list) or isinstance(v, tuple):
                self._document.ClearField(k)
                getattr(self._document, k).extend(v)
            elif isinstance(v, dict):
                self._document.ClearField(k)
                getattr(self._document, k).update(v)
            else:
                setattr(self, k, v)

    @property
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
    def text(self):
        return self._document.text

    @text.setter
    def text(self, value: str):
        self._document.text = value
        self.mime_type = 'text/plain'

    @property
    def uri(self) -> str:
        return self._document.uri

    @uri.setter
    def uri(self, value: str):
        """Set the URI of the document

        .. note::
            :attr:`mime_type` will be updated accordingly

        :param value: acceptable URI/URL, raise ``ValueError`` when it is not a valid URI
        :return:
        """
        scheme = urllib.parse.urlparse(value).scheme
        if ((scheme in {'http', 'https'} and is_url(value))
                or (scheme in {'data'})
                or os.path.exists(value)
                or os.access(os.path.dirname(value), os.W_OK)):
            self._document.uri = value
            self.mime_type = guess_mime(value)
        else:
            raise ValueError(f'{value} is not a valid URI')

    @property
    def mime_type(self) -> str:
        """Get MIME type of the document"""
        return self._document.mime_type

    @mime_type.setter
    def mime_type(self, value: str):
        """Set MIME type of the document

        :param value: the acceptable MIME type, raise ``ValueError`` when MIME type is not
                recognizable.
        """
        if value in mimetypes.types_map.values():
            self._document.mime_type = value
        elif value:
            # given but not recognizable, do best guess
            r = mimetypes.guess_type(f'*.{value}')[0]
            if r:
                self._document.mime_type = r
            else:
                raise ValueError(f'{value} is not a valid MIME type')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.update_id()

    @property
    def content(self) -> DocumentContentType:
        attr = self._document.WhichOneof('content')
        if attr:
            return getattr(self, attr)

    @content.setter
    def content(self, value: DocumentContentType):
        if isinstance(value, bytes):
            self.buffer = value
        elif isinstance(value, str):
            self.text = value
        elif isinstance(value, np.ndarray):
            self.blob = value
