import mimetypes
import os
import re
import urllib.parse
import warnings
from typing import Union, Dict, Iterator, Optional, TypeVar

import numpy as np
from google.protobuf import json_format

from .uid import *
from ..ndarray.generic import NdArray
from ...excepts import BadDocType
from ...helper import is_url, typename, guess_mime
from ...importer import ImportExtensions
from ...proto import jina_pb2

_empty_doc = jina_pb2.DocumentProto()
_id_regex = re.compile(r'[0-9a-fA-F]{16}')
__all__ = ['Document', 'DocumentContentType', 'DocumentSourceType']

DocumentContentType = TypeVar('DocumentContentType', bytes, str, np.ndarray, jina_pb2.NdArrayProto, NdArray)
DocumentSourceType = TypeVar('DocumentSourceType',
                             jina_pb2.DocumentProto, bytes, str, Dict)


class Document:
    """
    :class:`Document` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.jina_pb2.DocumentProto` object without working with Protobuf itself.

    To create a :class:`Document` object, simply:

        .. highlight:: python
        .. code-block:: python

            from jina import Document
            d = Document()
            d.text = 'abc'

    Jina requires each Document to have a string id. You can use :meth:`update_id` or simply
    use :class:`Document` as a context manager:

        .. highlight:: python
        .. code-block:: python

            with Document() as d:
                d.text = 'hello'

            assert d.id  # now `id` has value

    To access and modify the content of the document, you can use :attr:`text`, :attr:`blob`, and :attr:`buffer`.
    Each property is implemented with proper setter, to improve the integrity and user experience. For example,
    assigning ``doc.blob`` or ``doc.embedding`` can be simply done via:

        .. highlight:: python
        .. code-block:: python

            import numpy as np

            # to set as content
            d.content = np.random.random([10, 5])

            # to set as embedding
            d.embedding = np.random.random([10, 5])

    It also provides multiple way to extract from existing Document. You can build :class:`Document`
    from ``jina_pb2.DocumentProto``, ``bytes``, ``str``, and ``Dict``. You can also use it as view (i.e.
    weak reference when building from an existing ``jina_pb2.DocumentProto``). For example,

        .. highlight:: python
        .. code-block:: python

            a = DocumentProto()
            b = Document(a, copy=False)
            a.text = 'hello'
            assert b.text == 'hello'

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
        try:
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
                # directly parsing from binary string gives large false-positive
                # fortunately protobuf throws a warning when the parsing seems go wrong
                # the context manager below converts this warning into exception and throw it
                # properly
                with warnings.catch_warnings():
                    warnings.filterwarnings('error',
                                            'Unexpected end-group tag',
                                            category=RuntimeWarning)
                    try:
                        self._document.ParseFromString(document)
                    except RuntimeWarning as ex:
                        raise BadDocType('fail to construct a document') from ex
            elif document is not None:
                # note ``None`` is not considered as a bad type
                raise ValueError(f'{typename(document)} is not recognizable')
        except Exception as ex:
            raise BadDocType('fail to construct a document') from ex

        self.update(**kwargs)

    def __getattr__(self, name: str):
        if hasattr(_empty_doc, name):
            return getattr(self._document, name)
        else:
            raise AttributeError

    def update_id(self):
        """Update the document id according to its content.

        .. warning::
            To fully consider the content in this document, please use this function after
            you have fully modified the Document, not right way after create the Document.

            If you are using Document as context manager, then no need to call this function manually.
            Simply

            .. highlight:: python
            .. code-block:: python

                with Document() as d:
                    d.text = 'hello'

                assert d.id  # now `id` has value

        """
        self._document.id = new_doc_id(self._document)

    @property
    def id_in_hash(self) -> int:
        """The document id in the integer form of bytes, as 8 bytes map to int64.
        This is useful when sometimes you want to use key along with other numeric values together in one ndarray,
        such as ranker and Numpyindexer
        """
        return id2hash(self._document.id)

    @property
    def id_in_bytes(self) -> bytes:
        """The document id in the binary format of str, it has 8 bytes fixed length,
        so it can be used in the dense file storage, e.g. BinaryPbIndexer,
        as it requires the key has to be fixed length.
        """
        return id2bytes(self._document.id)

    @property
    def length(self) -> int:
        # TODO(Han): rename this to siblings as this shadows the built-in `length`
        return self._document.length

    @length.setter
    def length(self, value: int):
        self._document.length = value

    @property
    def id(self) -> str:
        """The document id in hex string, for non-binary environment such as HTTP, CLI, HTML and also human-readable.
        it will be used as the major view.
        """
        return self._document.id

    @id.setter
    def id(self, value: str):
        """Set document id to a string value

        .. note:

            Customized ``id`` is acceptable as long as
            - it only contains the symbols "0"–"9" to represent values 0 to 9,
            and "A"–"F" (or alternatively "a"–"f").
            - it has 16 chars described above.

        :param value: restricted string value
        :return:
        """
        if not isinstance(value, str) or not _id_regex.match(value):
            raise ValueError('Customized ``id`` is only acceptable when: \
            - it only contains chars "0"–"9" to represent values 0 to 9, \
            and "A"–"F" (or alternatively "a"–"f"). \
            - it has 16 chars described above.')
        else:
            self._document.id = value

    @property
    def blob(self) -> 'np.ndarray':
        """Return ``blob``, one of the content form of a Document.

        .. note::
            Use :attr:`content` to return the content of a Document
        """
        return NdArray(self._document.blob).value

    @blob.setter
    def blob(self, value: Union['np.ndarray', 'jina_pb2.NdArrayProto', 'NdArray']):
        self._update_ndarray('blob', value)

    @property
    def embedding(self) -> 'np.ndarray':
        """Return ``embedding`` of the content of a Document.
        """
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
        """Return ``buffer``, one of the content form of a Document.

        .. note::
            Use :attr:`content` to return the content of a Document
        """
        return self._document.buffer

    @buffer.setter
    def buffer(self, value: bytes):
        self._document.buffer = value
        if self._document.buffer:
            with ImportExtensions(required=False,
                                  pkg_name='python-magic',
                                  help_text=f'can not sniff the MIME type '
                                            f'MIME sniffing requires brew install '
                                            f'libmagic (Mac)/ apt-get install libmagic1 (Linux)'):
                import magic
                self._document.mime_type = magic.from_buffer(value, mime=True)

    @property
    def text(self):
        """Return ``text``, one of the content form of a Document.

        .. note::
            Use :attr:`content` to return the content of a Document
        """
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
        """Return the content of the document. It checks whichever field among :attr:`blob`, :attr:`text`,
        :attr:`buffer` has value and return it.

        .. seealso::
            :attr:`blob`, :attr:`buffer`, :attr:`text`
        """
        attr = self._document.WhichOneof('content')
        if attr:
            return getattr(self, attr)

    @content.setter
    def content(self, value: DocumentContentType):
        """Set the content of the document. It assigns the value to field with the right type.

        .. seealso::
            :attr:`blob`, :attr:`buffer`, :attr:`text`
        """
        if isinstance(value, bytes):
            self.buffer = value
        elif isinstance(value, str):
            # TODO(Han): this implicit fallback is too much but that's
            #  how the original _generate function implement. And a lot of
            #  tests depend on this logic. Stay in this
            #  way to keep all tests passing until I got time to refactor this part
            try:
                self.uri = value
            except ValueError:
                self.text = value
        elif isinstance(value, np.ndarray):
            self.blob = value
        else:
            # ``None`` is also considered as bad type
            raise TypeError(f'{typename(value)} is not recognizable')
