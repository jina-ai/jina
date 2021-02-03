import base64
import mimetypes
import os
import urllib.parse
import urllib.request
import warnings
from hashlib import blake2b
from typing import Union, Dict, Optional, TypeVar, Any, Callable, Sequence, Tuple

import numpy as np
from google.protobuf import json_format
from google.protobuf.field_mask_pb2 import FieldMask

from .converters import png_to_buffer, to_datauri, guess_mime
from .uid import DIGEST_SIZE, UniqueId
from ..mixin import ProtoTypeMixin
from ..ndarray.generic import NdArray
from ..score import NamedScore
from ..sets.chunk import ChunkSet
from ..sets.match import MatchSet
from ...excepts import BadDocType
from ...helper import is_url, typename, random_identity
from ...importer import ImportExtensions
from ...proto import jina_pb2

__all__ = ['Document', 'DocumentContentType', 'DocumentSourceType']

DocumentContentType = TypeVar('DocumentContentType', bytes, str, np.ndarray)
DocumentSourceType = TypeVar('DocumentSourceType',
                             jina_pb2.DocumentProto, bytes, str, Dict)


class Document(ProtoTypeMixin):
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

    Jina requires each Document to have a string id. You can set a custom one,
    or if non has been set a random one will be assigned.

    Or you can use :class:`Document` as a context manager:

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

    MIME type is auto set/guessed when setting :attr:`content` and :attr:`uri`

    :class:`Document` also provides multiple way to build from existing Document. You can build :class:`Document`
    from ``jina_pb2.DocumentProto``, ``bytes``, ``str``, and ``Dict``. You can also use it as view (i.e.
    weak reference when building from an existing ``jina_pb2.DocumentProto``). For example,

        .. highlight:: python
        .. code-block:: python

            a = DocumentProto()
            b = Document(a, copy=False)
            a.text = 'hello'
            assert b.text == 'hello'

    You can leverage the :meth:`convert_a_to_b` interface to convert between content forms.

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
        self._pb_body = jina_pb2.DocumentProto()
        try:
            if isinstance(document, jina_pb2.DocumentProto):
                if copy:
                    self._pb_body.CopyFrom(document)
                else:
                    self._pb_body = document
            elif isinstance(document, dict):
                json_format.ParseDict(document, self._pb_body)
            elif isinstance(document, str):
                json_format.Parse(document, self._pb_body)
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
                        self._pb_body.ParseFromString(document)
                    except RuntimeWarning as ex:
                        raise BadDocType(f'fail to construct a document from {document}') from ex
            elif isinstance(document, Document):
                if copy:
                    self._pb_body.CopyFrom(document.proto)
                else:
                    self._pb_body = document.proto
            elif document is not None:
                # note ``None`` is not considered as a bad type
                raise ValueError(f'{typename(document)} is not recognizable')
        except Exception as ex:
            raise BadDocType(f'fail to construct a document from {document}, '
                             f'if you are trying to set the content '
                             f'you may use "Document(content=your_content)"') from ex

        if self._pb_body.id is None or not self._pb_body.id:
            self.id = random_identity(use_uuid1=True)

        self.set_attrs(**kwargs)

    @property
    def length(self) -> int:
        # TODO(Han): rename this to siblings as this shadows the built-in `length`
        return self._pb_body.length

    @length.setter
    def length(self, value: int):
        self._pb_body.length = value

    @property
    def weight(self) -> float:
        """Returns the weight of the document """
        return self._pb_body.weight

    @weight.setter
    def weight(self, value: float):
        """Set the weight of the document

        :param value: the float weight of the document.
        """
        self._pb_body.weight = value

    @property
    def modality(self) -> str:
        """Get the modality of the document """
        return self._pb_body.modality

    @modality.setter
    def modality(self, value: str):
        """Set the modality of the document"""
        self._pb_body.modality = value

    @property
    def content_hash(self):
        return self._pb_body.content_hash

    def update_content_hash(self,
                            exclude_fields: Optional[Tuple[str]] = (
                                    'id', 'chunks', 'matches', 'content_hash', 'parent_id'),
                            include_fields: Optional[Tuple[str]] = None) -> None:
        """Update the document hash according to its content.

        :param exclude_fields: a tuple of field names that excluded when computing content hash
        :param include_fields: a tuple of field names that included when computing content hash

        .. note::
            "exclude_fields" and "include_fields" are mutually exclusive, use one only
        """
        masked_d = jina_pb2.DocumentProto()
        masked_d.CopyFrom(self._pb_body)
        empty_doc = jina_pb2.DocumentProto()
        if include_fields and exclude_fields:
            raise ValueError('"exclude_fields" and "exclude_fields" are mutually exclusive, use one only')

        if include_fields is not None:
            FieldMask(paths=include_fields).MergeMessage(masked_d, empty_doc)
            masked_d = empty_doc
        elif exclude_fields is not None:
            FieldMask(paths=exclude_fields).MergeMessage(empty_doc, masked_d, replace_repeated_field=True)

        self._pb_body.content_hash = blake2b(masked_d.SerializeToString(), digest_size=DIGEST_SIZE).hexdigest()

    @property
    def id(self) -> str:
        """The document id in hex string, for non-binary environment such as HTTP, CLI, HTML and also human-readable.
        it will be used as the major view.
        """
        return self._pb_body.id

    @property
    def parent_id(self) -> str:
        """The document's parent id in hex string, for non-binary environment such as HTTP, CLI, HTML and also human-readable.
        it will be used as the major view.
        """
        return self._pb_body.parent_id

    @id.setter
    def id(self, value: Union[bytes, str, int]):
        """Set document id to a string value

        .. note:

            Customized ``id`` is acceptable as long as
            - it only contains the symbols "0"–"9" to represent values 0 to 9,
            and "A"–"F" (or alternatively "a"–"f").
            - it has 16 chars described above.

        :param value: restricted string value
        :return:
        """
        if isinstance(value, str):
            self._pb_body.id = value
        else:
            warnings.warn(f'expecting a string as ID, receiving {type(value)}. '
                          f'Note this type will be deprecated soon', DeprecationWarning)
            self._pb_body.id = UniqueId(value)

    @parent_id.setter
    def parent_id(self, value: Union[bytes, str, int]):
        """Set document's parent id to a string value

        .. note:

            Customized ``id`` is acceptable as long as
            - it only contains the symbols "0"–"9" to represent values 0 to 9,
            and "A"–"F" (or alternatively "a"–"f").
            - it has 16 chars described above.

        :param value: restricted string value
        :return:
        """
        if isinstance(value, str):
            self._pb_body.parent_id = value
        else:
            warnings.warn(f'expecting a string as ID, receiving {type(value)}. '
                          f'Note this type will be deprecated soon', DeprecationWarning)
            self._pb_body.parent_id = UniqueId(value)

    @property
    def blob(self) -> 'np.ndarray':
        """Return ``blob``, one of the content form of a Document.

        .. note::
            Use :attr:`content` to return the content of a Document
        """
        return NdArray(self._pb_body.blob).value

    @blob.setter
    def blob(self, value: Union['np.ndarray', 'jina_pb2.NdArrayProto', 'NdArray']):
        self._update_ndarray('blob', value)

    @property
    def embedding(self) -> 'np.ndarray':
        """Return ``embedding`` of the content of a Document.
        """
        return NdArray(self._pb_body.embedding).value

    @embedding.setter
    def embedding(self, value: Union['np.ndarray', 'jina_pb2.NdArrayProto', 'NdArray']):
        self._update_ndarray('embedding', value)

    def _update_ndarray(self, k, v):
        if isinstance(v, jina_pb2.NdArrayProto):
            getattr(self._pb_body, k).CopyFrom(v)
        elif isinstance(v, np.ndarray):
            NdArray(getattr(self._pb_body, k)).value = v
        elif isinstance(v, NdArray):
            NdArray(getattr(self._pb_body, k)).is_sparse = v.is_sparse
            NdArray(getattr(self._pb_body, k)).value = v.value
        else:
            raise TypeError(f'{k} is in unsupported type {typename(v)}')

    @property
    def matches(self) -> 'MatchSet':
        """Get all matches of the current document """
        return MatchSet(self._pb_body.matches, reference_doc=self)

    @property
    def chunks(self) -> 'ChunkSet':
        """Get all chunks of the current document """
        return ChunkSet(self._pb_body.chunks, reference_doc=self)

    def set_attrs(self, **kwargs):
        """Bulk update Document fields with key-value specified in kwargs

        .. seealso::
            :meth:`get_attrs` for bulk get attributes

        """
        for k, v in kwargs.items():
            if isinstance(v, list) or isinstance(v, tuple):
                if k == 'chunks':
                    self.chunks.extend(v)
                elif k == 'matches':
                    self.matches.extend(v)
                else:
                    self._pb_body.ClearField(k)
                    getattr(self._pb_body, k).extend(v)
            elif isinstance(v, dict):
                self._pb_body.ClearField(k)
                getattr(self._pb_body, k).update(v)
            else:
                if hasattr(Document, k) and isinstance(getattr(Document, k), property) and getattr(Document, k).fset:
                    # if class property has a setter
                    setattr(self, k, v)
                elif hasattr(self._pb_body, k):
                    # no property setter, but proto has this attribute so fallback to proto
                    setattr(self._pb_body, k, v)
                else:
                    raise AttributeError(f'{k} is not recognized')

    def get_attrs(self, *args) -> Dict[str, Any]:
        """Bulk fetch Document fields and return a dict of the key-value pairs

        .. seealso::
            :meth:`update` for bulk set/update attributes

        """
        return {k: getattr(self, k) for k in args if hasattr(self, k)}

    @property
    def buffer(self) -> bytes:
        """Return ``buffer``, one of the content form of a Document.

        .. note::
            Use :attr:`content` to return the content of a Document
        """
        return self._pb_body.buffer

    @buffer.setter
    def buffer(self, value: bytes):
        self._pb_body.buffer = value
        if value:
            with ImportExtensions(required=False,
                                  pkg_name='python-magic',
                                  help_text=f'can not sniff the MIME type '
                                            f'MIME sniffing requires brew install '
                                            f'libmagic (Mac)/ apt-get install libmagic1 (Linux)'):
                import magic
                self._pb_body.mime_type = magic.from_buffer(value, mime=True)

    @property
    def text(self):
        """Return ``text``, one of the content form of a Document.

        .. note::
            Use :attr:`content` to return the content of a Document
        """
        return self._pb_body.text

    @text.setter
    def text(self, value: str):
        self._pb_body.text = value
        self.mime_type = 'text/plain'

    @property
    def uri(self) -> str:
        return self._pb_body.uri

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
            self._pb_body.uri = value
            self.mime_type = guess_mime(value)
        else:
            raise ValueError(f'{value} is not a valid URI')

    @property
    def mime_type(self) -> str:
        """Get MIME type of the document"""
        return self._pb_body.mime_type

    @mime_type.setter
    def mime_type(self, value: str):
        """Set MIME type of the document

        :param value: the acceptable MIME type, raise ``ValueError`` when MIME type is not
                recognizable.
        """
        if value in mimetypes.types_map.values():
            self._pb_body.mime_type = value
        elif value:
            # given but not recognizable, do best guess
            r = mimetypes.guess_type(f'*.{value}')[0]
            if r:
                self._pb_body.mime_type = r
            else:
                raise ValueError(f'{value} is not a valid MIME type')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.update_content_hash()

    @property
    def content_type(self) -> str:
        """Return the content type of the document, possible values: text, blob, buffer"""
        return self._pb_body.WhichOneof('content')

    @property
    def content(self) -> DocumentContentType:
        """Return the content of the document. It checks whichever field among :attr:`blob`, :attr:`text`,
        :attr:`buffer` has value and return it.

        .. seealso::
            :attr:`blob`, :attr:`buffer`, :attr:`text`
        """
        attr = self.content_type
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

    @property
    def granularity(self):
        return self._pb_body.granularity

    @granularity.setter
    def granularity(self, granularity_value: int):
        self._pb_body.granularity = granularity_value

    @property
    def score(self):
        return self._pb_body.score

    @score.setter
    def score(self, value: Union[jina_pb2.NamedScoreProto, NamedScore]):
        if isinstance(value, jina_pb2.NamedScoreProto):
            self._pb_body.score.CopyFrom(value)
        elif isinstance(value, NamedScore):
            self._pb_body.score.CopyFrom(value._pb_body)
        else:
            raise TypeError(f'score is in unsupported type {typename(value)}')

    def convert_buffer_to_blob(self, **kwargs):
        """Assuming the :attr:`buffer` is a _valid_ buffer of Numpy ndarray,
        set :attr:`blob` accordingly.

        :param kwargs: reserved for maximum compatibility when using with ConvertDriver

        .. note::
            One can only recover values not shape information from pure buffer.
        """
        self.blob = np.frombuffer(self.buffer)

    def convert_blob_to_uri(self, width: int, height: int, resize_method: str = 'BILINEAR', **kwargs):
        """Assuming :attr:`blob` is a _valid_ image, set :attr:`uri` accordingly"""
        png_bytes = png_to_buffer(self.blob, width, height, resize_method)
        self.uri = 'data:image/png;base64,' + base64.b64encode(png_bytes).decode()

    def convert_uri_to_buffer(self, **kwargs):
        """Convert uri to buffer
        Internally it downloads from the URI and set :attr:`buffer`.

        :param kwargs: reserved for maximum compatibility when using with ConvertDriver

        """
        if urllib.parse.urlparse(self.uri).scheme in {'http', 'https', 'data'}:
            req = urllib.request.Request(self.uri, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as fp:
                self.buffer = fp.read()
        elif os.path.exists(self.uri):
            with open(self.uri, 'rb') as fp:
                self.buffer = fp.read()
        else:
            raise FileNotFoundError(f'{self.uri} is not a URL or a valid local path')

    def convert_uri_to_data_uri(self, charset: str = 'utf-8', base64: bool = False, **kwargs):
        """ Convert uri to data uri.
        Internally it reads uri into buffer and convert it to data uri

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit. Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that frequently uses non-US-ASCII characters.
        :param kwargs: reserved for maximum compatibility when using with ConvertDriver
        """
        self.convert_uri_to_buffer()
        self.uri = to_datauri(self.mime_type, self.buffer, charset, base64, binary=True)

    def convert_buffer_to_uri(self, charset: str = 'utf-8', base64: bool = False, **kwargs):
        """ Convert buffer to data uri.
        Internally it first reads into buffer and then converts it to data URI.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit.
         Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that
         frequently uses non-US-ASCII characters.
        :param kwargs: reserved for maximum compatibility when using with ConvertDriver
        """

        if not self.mime_type:
            raise ValueError(f'{self.mime_type} is unset, can not convert it to data uri')

        self.uri = to_datauri(self.mime_type, self.buffer, charset, base64, binary=True)

    def convert_text_to_uri(self, charset: str = 'utf-8', base64: bool = False, **kwargs):
        """ Convert text to data uri.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit.
        Designed to be efficient for non-text 8 bit and binary data.
        Sometimes used for text data that frequently uses non-US-ASCII characters.
        :param kwargs: reserved for maximum compatibility when using with ConvertDriver
        """

        self.uri = to_datauri(self.mime_type, self.text, charset, base64, binary=False)

    def convert_uri_to_text(self, **kwargs):
        """Assuming URI is text, convert it to text

        :param kwargs: reserved for maximum compatibility when using with ConvertDriver
        """
        self.convert_uri_to_buffer()
        self.text = self.buffer.decode()

    def convert_content_to_uri(self, **kwargs):
        """Convert content in URI with best effort

        :param kwargs: reserved for maximum compatibility when using with ConvertDriver
        """
        if self.text:
            self.convert_text_to_uri()
        elif self.buffer:
            self.convert_buffer_to_uri()
        elif self.content_type:
            raise NotImplementedError

    def MergeFrom(self, doc: 'Document'):
        self._pb_body.MergeFrom(doc.proto)

    def CopyFrom(self, doc: 'Document'):
        self._pb_body.CopyFrom(doc.proto)

    def traverse(self, traversal_path: str, callback_fn: Callable, *args, **kwargs) -> None:
        """Traverse leaves of the document."""
        from ..sets import DocumentSet
        self._traverse_rec(DocumentSet([self]), None, None, traversal_path, callback_fn, *args, **kwargs)

    def _traverse_rec(self, docs: Sequence['Document'], parent_doc: Optional['Document'],
                      parent_edge_type: Optional[str], traversal_path: str, callback_fn: Callable, *args, **kwargs):
        if traversal_path:
            next_edge = traversal_path[0]
            for doc in docs:
                if next_edge == 'm':
                    self._traverse_rec(
                        doc.matches, doc, 'matches', traversal_path[1:], callback_fn, *args, **kwargs
                    )
                elif next_edge == 'c':
                    self._traverse_rec(
                        doc.chunks, doc, 'chunks', traversal_path[1:], callback_fn, *args, **kwargs
                    )
                else:
                    raise ValueError(f'"{next_edge}" in "{traversal_path}" is not a valid traversal path')
        else:
            for d in docs:
                callback_fn(d, parent_doc, parent_edge_type, *args, **kwargs)
