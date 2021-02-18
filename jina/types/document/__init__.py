import base64
import io
import json
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

from .converters import png_to_buffer, to_datauri, guess_mime, to_image_blob
from ..mixin import ProtoTypeMixin
from ..ndarray.generic import NdArray
from ..score import NamedScore
from ..sets.chunk import ChunkSet
from ..sets.match import MatchSet
from ..querylang.queryset.dunderkey import dunder_get
from ...excepts import BadDocType
from ...helper import is_url, typename, random_identity, download_mermaid_url
from ...importer import ImportExtensions
from ...proto import jina_pb2
from ...logging import default_logger

__all__ = ['Document', 'DocumentContentType', 'DocumentSourceType']
DIGEST_SIZE = 8

DocumentContentType = TypeVar('DocumentContentType', bytes, str, np.ndarray)
DocumentSourceType = TypeVar('DocumentSourceType',
                             jina_pb2.DocumentProto, bytes, str, Dict)

_document_fields = set(list(jina_pb2.DocumentProto().DESCRIPTOR.fields_by_camelcase_name) + list(
    jina_pb2.DocumentProto().DESCRIPTOR.fields_by_name))


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
                 field_resolver: Dict[str, str] = None,
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
        :param field_resolver: a map from field names defined in ``document`` (JSON, dict) to the field
                names defined in Protobuf. This is only used when the given ``document`` is
                a JSON string or a Python dict.
        :param kwargs: other parameters to be set _after_ the document is constructed

        .. note::

            When ``document`` is a JSON string or Python dictionary object, the constructor will only map the values
            from known fields defined in Protobuf, all unknown fields are mapped to ``document.tags``. For example,

            .. highlight:: python
            .. code-block:: python

                d = Document({'id': '123', 'hello': 'world', 'tags': {'good': 'bye'}})

                assert d.id == '123'  # true
                assert d.tags['hello'] == 'world'  # true
                assert d.tags['good'] == 'bye'  # true
        """
        self._pb_body = jina_pb2.DocumentProto()
        try:
            if isinstance(document, jina_pb2.DocumentProto):
                if copy:
                    self._pb_body.CopyFrom(document)
                else:
                    self._pb_body = document
            elif isinstance(document, (dict, str)):
                if isinstance(document, str):
                    document = json.loads(document)

                if field_resolver:
                    document = {field_resolver.get(k, k): v for k, v in document.items()}

                user_fields = set(document.keys())
                if _document_fields.issuperset(user_fields):
                    json_format.ParseDict(document, self._pb_body)
                else:
                    _intersect = _document_fields.intersection(user_fields)
                    _remainder = user_fields.difference(_intersect)
                    if _intersect:
                        json_format.ParseDict({k: document[k] for k in _intersect}, self._pb_body)
                    if _remainder:
                        self._pb_body.tags.update({k: document[k] for k in _remainder})
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
        self._mermaid_id = random_identity()  #: for mermaid visualize id

    @property
    def length(self) -> int:
        """Get the length of of the document."""
        # TODO(Han): rename this to siblings as this shadows the built-in `length`
        return self._pb_body.length

    @length.setter
    def length(self, value: int):
        """
        Set the length of of the document.

        :param value: The int length of the document
        """
        self._pb_body.length = value

    @property
    def weight(self) -> float:
        """Return the weight of the document."""
        return self._pb_body.weight

    @weight.setter
    def weight(self, value: float):
        """Set the weight of the document.

        :param value: the float weight of the document.
        """
        self._pb_body.weight = value

    @property
    def modality(self) -> str:
        """Get the modality of the document."""
        return self._pb_body.modality

    @modality.setter
    def modality(self, value: str):
        """Set the modality of the document."""
        self._pb_body.modality = value

    @property
    def content_hash(self):
        """Get the content hash of the document."""
        return self._pb_body.content_hash

    @staticmethod
    def _update(source: 'Document',
                destination: 'Document',
                exclude_fields: Optional[Tuple[str]] = None,
                include_fields: Optional[Tuple[str]] = None,
                replace_message_field: bool = True,
                replace_repeated_field: bool = True) -> None:
        """Merge fields specified in ``include_fields`` or ``exclude_fields`` from source to destination.

        :param source: source :class:`Document` object.
        :param destination: the destination :class:`Document` object to be merged into.
        :param exclude_fields: a tuple of field names that excluded from destination document
        :param include_fields: a tuple of field names that included from source document
        :param replace_message_field: Replace message field if True. Merge message
                  field if False.
        :param replace_repeated_field: Replace repeated field if True. Append
                  elements of repeated field if False.

        .. note::
            *. if neither ``exclude_fields`` nor ``include_fields`` is given,
                then destination is overrided by the source completely.
            *. ``destination`` will be modified in place, ``source`` will be unchanged
        """

        if not include_fields and not exclude_fields:
            # same behavior as copy
            destination.CopyFrom(source)
        elif include_fields is not None and exclude_fields is None:
            FieldMask(paths=include_fields).MergeMessage(source.proto, destination.proto,
                                                         replace_message_field=replace_message_field,
                                                         replace_repeated_field=replace_repeated_field)
        elif exclude_fields is not None:
            empty_doc = jina_pb2.DocumentProto()

            _dest = jina_pb2.DocumentProto()
            # backup exclude fields in destination
            FieldMask(paths=exclude_fields).MergeMessage(destination.proto, _dest,
                                                         replace_repeated_field=True,
                                                         replace_message_field=True)

            if include_fields is None:
                # override dest with src
                destination.CopyFrom(source)
            else:
                # only update include fields
                FieldMask(paths=include_fields).MergeMessage(source.proto, destination.proto,
                                                             replace_message_field=replace_message_field,
                                                             replace_repeated_field=replace_repeated_field)

            # clear the exclude fields
            FieldMask(paths=exclude_fields).MergeMessage(empty_doc, destination.proto,
                                                         replace_repeated_field=True,
                                                         replace_message_field=True)

            # recover exclude fields
            destination.proto.MergeFrom(_dest)

    def update(self, source: 'Document',
               exclude_fields: Optional[Tuple[str, ...]] = None,
               include_fields: Optional[Tuple[str, ...]] = None) -> None:
        """Updates fields specified in ``include_fields`` from the source to current Document.

        :param source: source :class:`Document` object.
        :param exclude_fields: a tuple of field names that excluded from the current document,
                when not given the non-empty fields of the current document is considered as ``exclude_fields``
        :param include_fields: a tuple of field names that included from the source document

        .. note::
            *. ``destination`` will be modified in place, ``source`` will be unchanged
        """
        if (include_fields and not isinstance(include_fields, tuple)) or (
                exclude_fields and not isinstance(exclude_fields, tuple)):
            raise TypeError('include_fields and exclude_fields must be tuple of str')

        if exclude_fields is None:
            if include_fields:
                exclude_fields = tuple(f for f in self.non_empty_fields if f not in include_fields)
            else:
                exclude_fields = self.non_empty_fields

        if include_fields and exclude_fields:
            _intersect = set(include_fields).intersection(exclude_fields)
            if _intersect:
                raise ValueError(f'{_intersect} is in both `include_fields` and `exclude_fields`')

        self._update(source, self,
                     exclude_fields=exclude_fields,
                     include_fields=include_fields,
                     replace_message_field=True,
                     replace_repeated_field=True)

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
        """Set document id to a string value.

        :param value: id as bytes, int or str
        :return:
        """
        self._pb_body.id = str(value)

    @parent_id.setter
    def parent_id(self, value: Union[bytes, str, int]):
        """Set document's parent id to a string value.

        :param value: id as bytes, int or str
        :return:
        """
        self._pb_body.parent_id = str(value)

    @property
    def blob(self) -> 'np.ndarray':
        """Return ``blob``, one of the content form of a Document.

        .. note::
            Use :attr:`content` to return the content of a Document
        """
        return NdArray(self._pb_body.blob).value

    @blob.setter
    def blob(self, value: Union['np.ndarray', 'jina_pb2.NdArrayProto', 'NdArray']):
        """Set the `blob` to :param:`value`."""
        self._update_ndarray('blob', value)

    @property
    def embedding(self) -> 'np.ndarray':
        """Return ``embedding`` of the content of a Document."""
        return NdArray(self._pb_body.embedding).value

    @embedding.setter
    def embedding(self, value: Union['np.ndarray', 'jina_pb2.NdArrayProto', 'NdArray']):
        """Set the ``embedding`` of the content of a Document."""
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
        """Get all matches of the current document."""
        return MatchSet(self._pb_body.matches, reference_doc=self)

    @property
    def chunks(self) -> 'ChunkSet':
        """Get all chunks of the current document."""
        return ChunkSet(self._pb_body.chunks, reference_doc=self)

    def set_attrs(self, **kwargs):
        """Bulk update Document fields with key-value specified in kwargs

        .. seealso::
            :meth:`get_attrs` for bulk get attributes

        """
        for k, v in kwargs.items():
            if isinstance(v, (list, tuple)):
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

        .. note::
            Arguments will be extracted using `dunder_get`
            .. highlight:: python
            .. code-block:: python

                d = Document({'id': '123', 'hello': 'world', 'tags': {'id': 'external_id', 'good': 'bye'}})

                assert d.id == '123'  # true
                assert d.tags['hello'] == 'world' # true
                assert d.tags['good'] == 'bye' # true
                assert d.tags['id'] == 'external_id' # true

                res = d.get_attrs(*['id', 'tags__hello', 'tags__good', 'tags__id'])

                assert res['id'] == '123' # true
                assert res['tags__hello'] == 'world' # true
                assert res['tags__good'] == 'bye' # true
                assert res['tags__id'] == 'external_id' # true
        """

        ret = {}
        for k in args:

            try:
                if hasattr(self, k):
                    value = getattr(self, k)
                else:
                    value = dunder_get(self._pb_body, k)

                if value is None:
                    raise ValueError

                ret[k] = value
            except (AttributeError, ValueError):
                default_logger.warning(f'Could not get attribute `{typename(self)}.{k}`, returning `None`')
                ret[k] = None
        return ret

    @property
    def buffer(self) -> bytes:
        """Return ``buffer``, one of the content form of a Document.

        .. note::
            Use :attr:`content` to return the content of a Document
        """
        return self._pb_body.buffer

    @buffer.setter
    def buffer(self, value: bytes):
        """Set the ``buffer`` to :param:`value`."""
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
        """Set the `text` to :param:`value`"""
        self._pb_body.text = value
        self.mime_type = 'text/plain'

    @property
    def uri(self) -> str:
        """Return the URI of the document."""
        return self._pb_body.uri

    @uri.setter
    def uri(self, value: str):
        """Set the URI of the document.

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
        """Return the granularity of the document."""
        return self._pb_body.granularity

    @granularity.setter
    def granularity(self, granularity_value: int):
        """Set the granularity of the document."""
        self._pb_body.granularity = granularity_value

    @property
    def score(self):
        """Return the score of the document."""
        return NamedScore(self._pb_body.score)

    @score.setter
    def score(self, value: Union[jina_pb2.NamedScoreProto, NamedScore]):
        """Set the score of the document."""
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

    def convert_buffer_image_to_blob(self, color_axis: int = -1, **kwargs):
        """ Convert an image buffer to blob

        :param color_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        :param kwargs: reserved for maximum compatibility when using with ConvertDriver
        """
        self.blob = to_image_blob(io.BytesIO(self.buffer), color_axis)

    def convert_blob_to_uri(self, width: int, height: int, resize_method: str = 'BILINEAR', **kwargs):
        """Assuming :attr:`blob` is a _valid_ image, set :attr:`uri` accordingly"""
        png_bytes = png_to_buffer(self.blob, width, height, resize_method)
        self.uri = 'data:image/png;base64,' + base64.b64encode(png_bytes).decode()

    def convert_uri_to_blob(self, color_axis: int = -1, uri_prefix: str = None, **kwargs):
        """ Convert uri to blob

        :param color_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        :param kwargs: reserved for maximum compatibility when using with ConvertDriver
        """
        self.blob = to_image_blob((uri_prefix + self.uri) if uri_prefix else self.uri, color_axis)

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
        """Merge the content of target :param:doc into current document."""
        self._pb_body.MergeFrom(doc.proto)

    def CopyFrom(self, doc: 'Document'):
        """Copy the content of target :param:doc into current document."""
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

    def __mermaid_str__(self):
        results = []
        from google.protobuf.json_format import MessageToDict
        content = MessageToDict(self._pb_body, preserving_proto_field_name=True)

        _id = f'{self._mermaid_id[:3]}~Document~'

        for idx, c in enumerate(self.chunks):
            results.append(f'{_id} --> "{idx + 1}/{len(self.chunks)}" {c._mermaid_id[:3]}~Document~: chunks')
            results.append(c.__mermaid_str__())

        for idx, c in enumerate(self.matches):
            results.append(f'{_id} ..> "{idx + 1}/{len(self.matches)}" {c._mermaid_id[:3]}~Document~: matches')
            results.append(c.__mermaid_str__())
        if 'chunks' in content:
            content.pop('chunks')
        if 'matches' in content:
            content.pop('matches')
        if content:
            results.append(f'class {_id}{{')
            for k, v in content.items():
                if isinstance(v, (str, int, float, bytes)):
                    results.append(f'+{k} {str(v)[:10]}')
                else:
                    results.append(f'+{k}({type(getattr(self, k, v))})')
            results.append('}')

        return '\n'.join(results)

    def _mermaid_to_url(self, img_type) -> str:
        """
        Rendering the current flow as a url points to a SVG, it needs internet connection
        :param kwargs: keyword arguments of :py:meth:`to_mermaid`
        :return: the url points to a SVG
        """
        if img_type == 'jpg':
            img_type = 'img'

        mermaid_str = """
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#FFC666'}}}%%
classDiagram
        
        """ + self.__mermaid_str__()

        encoded_str = base64.b64encode(bytes(mermaid_str.strip(), 'utf-8')).decode('utf-8')

        return f'https://mermaid.ink/{img_type}/{encoded_str}'

    def _ipython_display_(self):
        """Displays the object in IPython as a side effect"""
        self.plot(inline_display=True)

    def plot(self, output: str = None,
             inline_display: bool = False) -> None:
        """
        Visualize the Document recursively.

        :param output: a filename specifying the name of the image to be created,
                    the suffix svg/jpg determines the file type of the output image
        :param inline_display: show image directly inside the Jupyter Notebook
        """
        image_type = 'svg'
        if output and output.endswith('jpg'):
            image_type = 'jpg'

        url = self._mermaid_to_url(image_type)
        showed = False
        if inline_display:
            try:
                from IPython.display import display, Image

                display(Image(url=url))
                showed = True
            except:
                # no need to panic users
                pass

        if output:
            download_mermaid_url(url, output)
        elif not showed:
            from jina.logging import default_logger
            default_logger.info(f'Document visualization: {url}')

    @property
    def non_empty_fields(self) -> Tuple[str]:
        """Return the set fields of the curren"""
        return tuple(field[0].name for field in self.ListFields())
