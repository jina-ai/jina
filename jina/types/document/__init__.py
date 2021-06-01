import base64
import io
import json
import mimetypes
import os
import urllib.parse
import urllib.request
import warnings
from hashlib import blake2b
from typing import (
    Iterable,
    Union,
    Dict,
    Optional,
    TypeVar,
    Any,
    Tuple,
    List,
    Type,
)

import numpy as np
from google.protobuf import json_format
from google.protobuf.field_mask_pb2 import FieldMask
from jina.types.struct import StructView

from .converters import png_to_buffer, to_datauri, guess_mime, to_image_blob
from ..arrays.chunk import ChunkArray
from ..arrays.match import MatchArray
from ..mixin import ProtoTypeMixin
from ..ndarray.generic import NdArray, BaseSparseNdArray
from ..score import NamedScore
from ...excepts import BadDocType
from ...helper import (
    typename,
    random_identity,
    download_mermaid_url,
    dunder_get,
)
from ...importer import ImportExtensions
from ...logging.predefined import default_logger
from ...proto import jina_pb2

if False:
    from scipy.sparse import coo_matrix

    # fix type-hint complain for sphinx and flake
    import scipy
    import tensorflow as tf
    import torch

    EmbeddingType = TypeVar(
        'EmbeddingType',
        np.ndarray,
        scipy.sparse.csr_matrix,
        scipy.sparse.coo_matrix,
        scipy.sparse.bsr_matrix,
        scipy.sparse.csc_matrix,
        torch.sparse_coo_tensor,
        tf.SparseTensor,
    )

    SparseEmbeddingType = TypeVar(
        'SparseEmbeddingType',
        np.ndarray,
        scipy.sparse.csr_matrix,
        scipy.sparse.coo_matrix,
        scipy.sparse.bsr_matrix,
        scipy.sparse.csc_matrix,
        torch.sparse_coo_tensor,
        tf.SparseTensor,
    )

__all__ = ['Document', 'DocumentContentType', 'DocumentSourceType']
DIGEST_SIZE = 8

DocumentContentType = TypeVar('DocumentContentType', bytes, str, np.ndarray)
DocumentSourceType = TypeVar(
    'DocumentSourceType', jina_pb2.DocumentProto, bytes, str, Dict
)

_all_mime_types = set(mimetypes.types_map.values())

_all_doc_content_keys = ('content', 'uri', 'blob', 'text', 'buffer')
_all_doc_array_keys = ('blob', 'embedding')


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

    def __init__(
        self,
        document: Optional[DocumentSourceType] = None,
        field_resolver: Dict[str, str] = None,
        copy: bool = False,
        **kwargs,
    ):
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

                def _update_doc(d: Dict):
                    for key in _all_doc_array_keys:
                        if key in d:
                            value = d[key]
                            if isinstance(value, list):
                                d[key] = NdArray(np.array(d[key])).dict()
                        if 'chunks' in d:
                            for chunk in d['chunks']:
                                _update_doc(chunk)
                        if 'matches' in d:
                            for match in d['matches']:
                                _update_doc(match)

                _update_doc(document)

                if field_resolver:
                    document = {
                        field_resolver.get(k, k): v for k, v in document.items()
                    }

                user_fields = set(document.keys())
                support_fields = set(
                    self.attributes(
                        include_proto_fields_camelcase=True, include_properties=False
                    )
                )

                if support_fields.issuperset(user_fields):
                    json_format.ParseDict(document, self._pb_body)
                else:
                    _intersect = support_fields.intersection(user_fields)
                    _remainder = user_fields.difference(_intersect)
                    if _intersect:
                        json_format.ParseDict(
                            {k: document[k] for k in _intersect}, self._pb_body
                        )
                    if _remainder:
                        support_prop = set(
                            self.attributes(
                                include_proto_fields=False, include_properties=True
                            )
                        )
                        _intersect2 = support_prop.intersection(_remainder)
                        _remainder2 = _remainder.difference(_intersect2)

                        if _intersect2:
                            self.set_attributes(**{p: document[p] for p in _intersect2})

                        if _remainder2:
                            self._pb_body.tags.update(
                                {k: document[k] for k in _remainder}
                            )
            elif isinstance(document, bytes):
                # directly parsing from binary string gives large false-positive
                # fortunately protobuf throws a warning when the parsing seems go wrong
                # the context manager below converts this warning into exception and throw it
                # properly
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        'error', 'Unexpected end-group tag', category=RuntimeWarning
                    )
                    try:
                        self._pb_body.ParseFromString(document)
                    except RuntimeWarning as ex:
                        raise BadDocType(
                            f'fail to construct a document from {document}'
                        ) from ex
            elif isinstance(document, Document):
                if copy:
                    self._pb_body.CopyFrom(document.proto)
                else:
                    self._pb_body = document.proto
            elif document is not None:
                # note ``None`` is not considered as a bad type
                raise ValueError(f'{typename(document)} is not recognizable')
        except Exception as ex:
            raise BadDocType(
                f'fail to construct a document from {document}, '
                f'if you are trying to set the content '
                f'you may use "Document(content=your_content)"'
            ) from ex

        if self._pb_body.id is None or not self._pb_body.id:
            self.id = random_identity(use_uuid1=True)

        # check if there are mutually exclusive content fields
        if _contains_conflicting_content(**kwargs):
            raise ValueError(
                f'Document content fields are mutually exclusive, please provide only one of {_all_doc_content_keys}'
            )
        self.set_attributes(**kwargs)
        self._mermaid_id = random_identity()  #: for mermaid visualize id

    def pop(self, *fields) -> None:
        """Remove the values from the given fields of this Document.

        :param fields: field names
        """
        for k in fields:
            self._pb_body.ClearField(k)

    def clear(self) -> None:
        """Remove all values from all fields of this Document."""
        self._pb_body.Clear()

    @property
    def siblings(self) -> int:
        """
        The number of siblings of the :class:``Document``

        .. # noqa: DAR201
        :getter: number of siblings
        :setter: number of siblings
        :type: int
        """
        return self._pb_body.siblings

    @siblings.setter
    def siblings(self, value: int):
        self._pb_body.siblings = value

    @property
    def weight(self) -> float:
        """
        :return: the weight of the document
        """
        return self._pb_body.weight

    @weight.setter
    def weight(self, value: float):
        """
        Set the weight of the document.

        :param value: the float weight of the document.
        """
        self._pb_body.weight = value

    @property
    def modality(self) -> str:
        """
        :return: the modality of the document."""
        return self._pb_body.modality

    @modality.setter
    def modality(self, value: str):
        """Set the modality of the document.

        :param value: The modality of the document
        """
        self._pb_body.modality = value

    @property
    def content_hash(self):
        """Get the content hash of the document.

        :return: the content_hash from the proto
        """
        return self._pb_body.content_hash

    @property
    def tags(self) -> Dict:
        """Return the `tags` field of this Document as a Python dict

        :return: a Python dict view of the tags.
        """
        return StructView(self._pb_body.tags)

    @tags.setter
    def tags(self, value: Dict):
        """Set the `tags` field of this Document to a Python dict

        :param value: a Python dict
        """
        self._pb_body.tags.Clear()
        self._pb_body.tags.update(value)

    def _update(
        self,
        source: 'Document',
        destination: 'Document',
        fields: Optional[List[str]] = None,
    ) -> None:
        """Merge fields specified in ``fields`` from source to destination.

        :param source: source :class:`Document` object.
        :param destination: the destination :class:`Document` object to be merged into.
        :param fields: a list of field names that included from destination document

        .. note::
            *. if ``fields`` is empty, then destination is overridden by the source completely.
            *. ``destination`` will be modified in place, ``source`` will be unchanged.
            *. the ``fields`` has value in destination while not in source will be preserved.
        """
        # We do a safe update: only update existent (value being set) fields from source.
        fields_can_be_updated = []
        # ListFields returns a list of (FieldDescriptor, value) tuples for present fields.
        present_fields = source._pb_body.ListFields()
        for field_descriptor, _ in present_fields:
            fields_can_be_updated.append(field_descriptor.name)
        if not fields:
            fields = fields_can_be_updated  # if `fields` empty, update all fields.
        for field in fields:
            if (
                field == 'tags'
            ):  # For the tags, stay consistent with the python update method.
                destination._pb_body.tags.update(source.tags)
            else:
                destination._pb_body.ClearField(field)
                setattr(destination, field, getattr(source, field))

    def update(
        self,
        source: 'Document',
        fields: Optional[List[str]] = None,
    ) -> None:
        """Updates fields specified in ``fields`` from the source to current Document.

        :param source: source :class:`Document` object.
        :param fields: a list of field names that included from the current document,
                if not specified, merge all fields.

        .. note::
            *. ``destination`` will be modified in place, ``source`` will be unchanged
        """
        if fields and not isinstance(fields, list):
            raise TypeError('Parameter `fields` must be list of str')
        self._update(
            source,
            self,
            fields=fields,
        )

    def update_content_hash(
        self,
        exclude_fields: Optional[Tuple[str]] = (
            'id',
            'chunks',
            'matches',
            'content_hash',
            'parent_id',
        ),
        include_fields: Optional[Tuple[str]] = None,
    ) -> None:
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
            raise ValueError(
                '"exclude_fields" and "exclude_fields" are mutually exclusive, use one only'
            )

        if include_fields is not None:
            FieldMask(paths=include_fields).MergeMessage(masked_d, empty_doc)
            masked_d = empty_doc
        elif exclude_fields is not None:
            FieldMask(paths=exclude_fields).MergeMessage(
                empty_doc, masked_d, replace_repeated_field=True
            )

        self._pb_body.content_hash = blake2b(
            masked_d.SerializeToString(), digest_size=DIGEST_SIZE
        ).hexdigest()

    @property
    def id(self) -> str:
        """The document id in hex string, for non-binary environment such as HTTP, CLI, HTML and also human-readable.
        it will be used as the major view.

        :return: the id from the proto
        """
        return self._pb_body.id

    @property
    def parent_id(self) -> str:
        """The document's parent id in hex string, for non-binary environment such as HTTP, CLI, HTML and also human-readable.
        it will be used as the major view.

        :return: the parent id from the proto
        """
        return self._pb_body.parent_id

    @id.setter
    def id(self, value: Union[bytes, str, int]):
        """Set document id to a string value.

        :param value: id as bytes, int or str
        """
        self._pb_body.id = str(value)

    @parent_id.setter
    def parent_id(self, value: Union[bytes, str, int]):
        """Set document's parent id to a string value.

        :param value: id as bytes, int or str
        """
        self._pb_body.parent_id = str(value)

    @property
    def blob(self) -> 'np.ndarray':
        """Return ``blob``, one of the content form of a Document.

        .. note::
            Use :attr:`content` to return the content of a Document

        :return: the blob content from the proto
        """
        return NdArray(self._pb_body.blob).value

    @blob.setter
    def blob(self, value: Union['np.ndarray', 'jina_pb2.NdArrayProto', 'NdArray']):
        """Set the `blob` to :param:`value`.

        :param value: the array value to set the blob
        """
        self._update_ndarray('blob', value)

    @property
    def embedding(self) -> 'EmbeddingType':
        """Return ``embedding`` of the content of a Document.

        :return: the embedding from the proto
        """
        return NdArray(self._pb_body.embedding).value

    def get_sparse_embedding(
        self, sparse_ndarray_cls_type: Type[BaseSparseNdArray], **kwargs
    ) -> 'SparseEmbeddingType':
        """Return ``embedding`` of the content of a Document as an sparse array.

        :param sparse_ndarray_cls_type: Sparse class type, such as `SparseNdArray`.
        :param kwargs: Additional key value argument, for `scipy` backend, we need to set
            the keyword `sp_format` as one of the scipy supported sparse format, such as `coo`
            or `csr`.
        :return: the embedding from the proto as an sparse array
        """
        return NdArray(
            self._pb_body.embedding,
            sparse_cls=sparse_ndarray_cls_type,
            is_sparse=True,
            **kwargs,
        ).value

    @embedding.setter
    def embedding(self, value: Union['np.ndarray', 'jina_pb2.NdArrayProto', 'NdArray']):
        """Set the ``embedding`` of the content of a Document.

        :param value: the array value to set the embedding
        """
        self._update_ndarray('embedding', value)

    def _update_sparse_ndarray(self, k, v, sparse_cls):
        NdArray(
            is_sparse=True,
            sparse_cls=sparse_cls,
            proto=getattr(self._pb_body, k),
        ).value = v

    def _check_installed_array_packages(self):
        from ... import JINA_GLOBAL

        if JINA_GLOBAL.scipy_installed is None:
            JINA_GLOBAL.scipy_installed = False
            with ImportExtensions(required=False, pkg_name='scipy'):
                import scipy

                JINA_GLOBAL.scipy_installed = True

        if JINA_GLOBAL.tensorflow_installed is None:
            JINA_GLOBAL.tensorflow_installed = False
            with ImportExtensions(required=False, pkg_name='tensorflow'):
                import tensorflow

                JINA_GLOBAL.tensorflow_installed = True

        if JINA_GLOBAL.torch_installed is None:
            JINA_GLOBAL.torch_installed = False
            with ImportExtensions(required=False, pkg_name='torch'):
                import torch

                JINA_GLOBAL.torch_installed = True

    def _update_if_sparse(self, k, v):

        from ... import JINA_GLOBAL

        v_valid_sparse_type = False
        self._check_installed_array_packages()

        if JINA_GLOBAL.scipy_installed:
            import scipy

            if scipy.sparse.issparse(v):
                from ..ndarray.sparse.scipy import SparseNdArray

                self._update_sparse_ndarray(k=k, v=v, sparse_cls=SparseNdArray)
                v_valid_sparse_type = True

        if JINA_GLOBAL.tensorflow_installed:
            import tensorflow

            if isinstance(v, tensorflow.SparseTensor):
                from ..ndarray.sparse.tensorflow import SparseNdArray

                self._update_sparse_ndarray(k=k, v=v, sparse_cls=SparseNdArray)
                v_valid_sparse_type = True

        if JINA_GLOBAL.torch_installed:
            import torch

            if isinstance(v, torch.Tensor) and v.is_sparse:
                from ..ndarray.sparse.pytorch import SparseNdArray

                self._update_sparse_ndarray(k=k, v=v, sparse_cls=SparseNdArray)
                v_valid_sparse_type = True

        return v_valid_sparse_type

    def _update_ndarray(self, k, v):
        if isinstance(v, jina_pb2.NdArrayProto):
            getattr(self._pb_body, k).CopyFrom(v)
        elif isinstance(v, np.ndarray):
            NdArray(getattr(self._pb_body, k)).value = v
        elif isinstance(v, NdArray):
            NdArray(getattr(self._pb_body, k)).is_sparse = v.is_sparse
            NdArray(getattr(self._pb_body, k)).value = v.value

        else:
            v_valid_sparse_type = self._update_if_sparse(k, v)

            if not v_valid_sparse_type:
                raise TypeError(f'{k} is in unsupported type {typename(v)}')

    @property
    def matches(self) -> 'MatchArray':
        """Get all matches of the current document.

        :return: the array of matches attached to this document
        """
        return MatchArray(self._pb_body.matches, reference_doc=self)

    @matches.setter
    def matches(self, value: Iterable['Document']):
        """Get all chunks of the current document.

        :param value: value to set
        """
        self.pop('matches')
        self.matches.extend(value)

    @property
    def chunks(self) -> 'ChunkArray':
        """Get all chunks of the current document.

        :return: the array of chunks of this document
        """
        return ChunkArray(self._pb_body.chunks, reference_doc=self)

    @chunks.setter
    def chunks(self, value: Iterable['Document']):
        """Get all chunks of the current document.

        :param value: the array of chunks of this document
        """
        self.pop('chunks')
        self.chunks.extend(value)

    def set_attributes(self, **kwargs):
        """Bulk update Document fields with key-value specified in kwargs

        .. seealso::
            :meth:`get_attrs` for bulk get attributes

        :param kwargs: the keyword arguments to set the values, where the keys are the fields to set
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
                if (
                    hasattr(Document, k)
                    and isinstance(getattr(Document, k), property)
                    and getattr(Document, k).fset
                ):
                    # if class property has a setter
                    setattr(self, k, v)
                elif hasattr(self._pb_body, k):
                    # no property setter, but proto has this attribute so fallback to proto
                    setattr(self._pb_body, k, v)
                else:
                    raise AttributeError(f'{k} is not recognized')

    def get_attributes(self, *fields: str) -> Union[Any, List[Any]]:
        """Bulk fetch Document fields and return a list of the values of these fields

        .. note::
            Arguments will be extracted using `dunder_get`
            .. highlight:: python
            .. code-block:: python

                d = Document({'id': '123', 'hello': 'world', 'tags': {'id': 'external_id', 'good': 'bye'}})

                assert d.id == '123'  # true
                assert d.tags['hello'] == 'world' # true
                assert d.tags['good'] == 'bye' # true
                assert d.tags['id'] == 'external_id' # true

                res = d.get_attrs_values(*['id', 'tags__hello', 'tags__good', 'tags__id'])

                assert res == ['123', 'world', 'bye', 'external_id']

        :param fields: the variable length values to extract from the document
        :return: a list with the attributes of this document ordered as the args
        """

        ret = []
        for k in fields:
            try:
                value = getattr(self, k)

                if value is None:
                    raise ValueError

                ret.append(value)
            except (AttributeError, ValueError):
                default_logger.warning(
                    f'Could not get attribute `{typename(self)}.{k}`, returning `None`'
                )
                ret.append(None)

        # unboxing if args is single
        if len(fields) == 1:
            ret = ret[0]

        return ret

    @property
    def buffer(self) -> bytes:
        """Return ``buffer``, one of the content form of a Document.

        .. note::
            Use :attr:`content` to return the content of a Document

        :return: the buffer bytes from this document
        """
        return self._pb_body.buffer

    @buffer.setter
    def buffer(self, value: bytes):
        """Set the ``buffer`` to :param:`value`.

        :param value: the bytes value to set the buffer
        """
        self._pb_body.buffer = value
        if value and not self._pb_body.mime_type:
            with ImportExtensions(
                required=False,
                pkg_name='python-magic',
                help_text=f'can not sniff the MIME type '
                f'MIME sniffing requires brew install '
                f'libmagic (Mac)/ apt-get install libmagic1 (Linux)',
            ):
                import magic

                self._pb_body.mime_type = magic.from_buffer(value, mime=True)

    @property
    def text(self):
        """Return ``text``, one of the content form of a Document.

        .. note::
            Use :attr:`content` to return the content of a Document

        :return: the text from this document content
        """
        return self._pb_body.text

    @text.setter
    def text(self, value: str):
        """Set the `text` to :param:`value`

        :param value: the text value to set as content
        """
        self._pb_body.text = value
        self.mime_type = 'text/plain'

    @property
    def uri(self) -> str:
        """Return the URI of the document.

        :return: the uri from this document proto
        """
        return self._pb_body.uri

    @uri.setter
    def uri(self, value: str):
        """Set the URI of the document.

        .. note::
            :attr:`mime_type` will be updated accordingly

        :param value: acceptable URI/URL, raise ``ValueError`` when it is not a valid URI
        """
        self._pb_body.uri = value
        self.mime_type = guess_mime(value)

    @property
    def mime_type(self) -> str:
        """Get MIME type of the document

        :return: the mime_type from this document proto
        """
        return self._pb_body.mime_type

    @mime_type.setter
    def mime_type(self, value: str):
        """Set MIME type of the document

        :param value: the acceptable MIME type, raise ``ValueError`` when MIME type is not
                recognizable.
        """
        if value in _all_mime_types:
            self._pb_body.mime_type = value
        elif value:
            # given but not recognizable, do best guess
            r = mimetypes.guess_type(f'*.{value}')[0]
            if r:
                self._pb_body.mime_type = r
            else:
                self._pb_body.mime_type = value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.update_content_hash()

    @property
    def content_type(self) -> str:
        """Return the content type of the document, possible values: text, blob, buffer

        :return: the type of content present in this document proto
        """
        return self._pb_body.WhichOneof('content')

    @property
    def content(self) -> DocumentContentType:
        """Return the content of the document. It checks whichever field among :attr:`blob`, :attr:`text`,
        :attr:`buffer` has value and return it.

        .. seealso::
            :attr:`blob`, :attr:`buffer`, :attr:`text`

        :return: the value of the content depending on `:meth:`content_type`
        """
        attr = self.content_type
        if attr:
            return getattr(self, attr)

    @content.setter
    def content(self, value: DocumentContentType):
        """Set the content of the document. It assigns the value to field with the right type.

        .. seealso::
            :attr:`blob`, :attr:`buffer`, :attr:`text`

        :param value: the value from which to set the content of the Document
        """
        if isinstance(value, bytes):
            self.buffer = value
        elif isinstance(value, str):
            if _is_uri(value):
                self.uri = value
            else:
                self.text = value
        elif isinstance(value, np.ndarray):
            self.blob = value
        else:
            # ``None`` is also considered as bad type
            raise TypeError(f'{typename(value)} is not recognizable')

    @property
    def granularity(self):
        """Return the granularity of the document.

        :return: the granularity from this document proto
        """
        return self._pb_body.granularity

    @granularity.setter
    def granularity(self, value: int):
        """Set the granularity of the document.

        :param value: the value of the granularity to be set
        """
        self._pb_body.granularity = value

    @property
    def adjacency(self):
        """Return the adjacency of the document.

        :return: the adjacency from this document proto
        """
        return self._pb_body.adjacency

    @adjacency.setter
    def adjacency(self, value: int):
        """Set the adjacency of the document.

        :param value: the value of the adjacency to be set
        """
        self._pb_body.adjacency = value

    @property
    def score(self):
        """Return the score of the document.

        :return: the score attached to this document as `:class:NamedScore`
        """
        return NamedScore(self._pb_body.score)

    @score.setter
    def score(
        self, value: Union[jina_pb2.NamedScoreProto, NamedScore, float, np.generic]
    ):
        """Set the score of the document.

        You can assign a scala variable directly.

        :param value: the value to set the score of the Document from
        """
        if isinstance(value, jina_pb2.NamedScoreProto):
            self._pb_body.score.CopyFrom(value)
        elif isinstance(value, NamedScore):
            self._pb_body.score.CopyFrom(value._pb_body)
        elif isinstance(value, (float, int)):
            self._pb_body.score.value = value
        elif isinstance(value, np.generic):
            self._pb_body.score.value = value.item()
        else:
            raise TypeError(f'score is in unsupported type {typename(value)}')

    def convert_image_buffer_to_blob(self, color_axis: int = -1):
        """Convert an image buffer to blob

        :param color_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        """
        self.blob = to_image_blob(io.BytesIO(self.buffer), color_axis)

    def convert_image_blob_to_uri(
        self, width: int, height: int, resize_method: str = 'BILINEAR'
    ):
        """Assuming :attr:`blob` is a _valid_ image, set :attr:`uri` accordingly
        :param width: the width of the blob
        :param height: the height of the blob
        :param resize_method: the resize method name
        """
        png_bytes = png_to_buffer(self.blob, width, height, resize_method)
        self.uri = 'data:image/png;base64,' + base64.b64encode(png_bytes).decode()

    def convert_image_uri_to_blob(
        self, color_axis: int = -1, uri_prefix: Optional[str] = None
    ):
        """Convert uri to blob

        :param color_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        :param uri_prefix: the prefix of the uri
        """
        self.blob = to_image_blob(
            (uri_prefix + self.uri) if uri_prefix else self.uri, color_axis
        )

    def convert_image_datauri_to_blob(self, color_axis: int = -1):
        """Convert data URI to image blob

        :param color_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        """
        req = urllib.request.Request(self.uri, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as fp:
            buffer = fp.read()
        self.blob = to_image_blob(io.BytesIO(buffer), color_axis)

    def convert_buffer_to_blob(self, dtype=None, count=-1, offset=0):
        """Assuming the :attr:`buffer` is a _valid_ buffer of Numpy ndarray,
        set :attr:`blob` accordingly.

        :param dtype: Data-type of the returned array; default: float.
        :param count: Number of items to read. ``-1`` means all data in the buffer.
        :param offset: Start reading the buffer from this offset (in bytes); default: 0.

        .. note::
            One can only recover values not shape information from pure buffer.
        """
        self.blob = np.frombuffer(self.buffer, dtype, count, offset)

    def convert_blob_to_buffer(self):
        """Convert blob to buffer"""
        self.buffer = self.blob.tobytes()

    def convert_uri_to_buffer(self):
        """Convert uri to buffer
        Internally it downloads from the URI and set :attr:`buffer`.

        """
        if urllib.parse.urlparse(self.uri).scheme in {'http', 'https', 'data'}:
            req = urllib.request.Request(
                self.uri, headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req) as fp:
                self.buffer = fp.read()
        elif os.path.exists(self.uri):
            with open(self.uri, 'rb') as fp:
                self.buffer = fp.read()
        else:
            raise FileNotFoundError(f'{self.uri} is not a URL or a valid local path')

    def convert_uri_to_datauri(self, charset: str = 'utf-8', base64: bool = False):
        """Convert uri to data uri.
        Internally it reads uri into buffer and convert it to data uri

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit. Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that frequently uses non-US-ASCII characters.
        """
        if not _is_datauri(self.uri):
            self.convert_uri_to_buffer()
            self.uri = to_datauri(
                self.mime_type, self.buffer, charset, base64, binary=True
            )

    def convert_buffer_to_uri(self, charset: str = 'utf-8', base64: bool = False):
        """Convert buffer to data uri.
        Internally it first reads into buffer and then converts it to data URI.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit.
            Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that
            frequently uses non-US-ASCII characters.
        """

        if not self.mime_type:
            raise ValueError(
                f'{self.mime_type} is unset, can not convert it to data uri'
            )

        self.uri = to_datauri(self.mime_type, self.buffer, charset, base64, binary=True)

    def convert_text_to_uri(self, charset: str = 'utf-8', base64: bool = False):
        """Convert text to data uri.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit.
            Designed to be efficient for non-text 8 bit and binary data.
            Sometimes used for text data that frequently uses non-US-ASCII characters.
        """

        self.uri = to_datauri(self.mime_type, self.text, charset, base64, binary=False)

    def convert_uri_to_text(self):
        """Assuming URI is text, convert it to text"""
        self.convert_uri_to_buffer()
        self.text = self.buffer.decode()

    def convert_content_to_uri(self):
        """Convert content in URI with best effort"""
        if self.text:
            self.convert_text_to_uri()
        elif self.buffer:
            self.convert_buffer_to_uri()
        elif self.content_type:
            raise NotImplementedError

    def MergeFrom(self, doc: 'Document'):
        """Merge the content of target

        :param doc: the document to merge from
        """
        self._pb_body.MergeFrom(doc.proto)

    def CopyFrom(self, doc: 'Document'):
        """Copy the content of target

        :param doc: the document to copy from
        """
        self._pb_body.CopyFrom(doc.proto)

    def __mermaid_str__(self):
        results = []
        from google.protobuf.json_format import MessageToDict

        content = MessageToDict(self._pb_body, preserving_proto_field_name=True)

        _id = f'{self._mermaid_id[:3]}~Document~'

        for idx, c in enumerate(self.chunks):
            results.append(
                f'{_id} --> "{idx + 1}/{len(self.chunks)}" {c._mermaid_id[:3]}~Document~: chunks'
            )
            results.append(c.__mermaid_str__())

        for idx, c in enumerate(self.matches):
            results.append(
                f'{_id} ..> "{idx + 1}/{len(self.matches)}" {c._mermaid_id[:3]}~Document~: matches'
            )
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

    def _mermaid_to_url(self, img_type: str) -> str:
        """
        Rendering the current flow as a url points to a SVG, it needs internet connection

        :param img_type: the type of image to be generated
        :return: the url pointing to a SVG
        """
        if img_type == 'jpg':
            img_type = 'img'

        mermaid_str = (
            """
                        %%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#FFC666'}}}%%
                        classDiagram
                    
                                """
            + self.__mermaid_str__()
        )

        encoded_str = base64.b64encode(bytes(mermaid_str.strip(), 'utf-8')).decode(
            'utf-8'
        )

        return f'https://mermaid.ink/{img_type}/{encoded_str}'

    def _ipython_display_(self):
        """Displays the object in IPython as a side effect"""
        self.plot(inline_display=True)

    def plot(self, output: Optional[str] = None, inline_display: bool = False) -> None:
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
            from jina.logging.predefined import default_logger

            default_logger.info(f'Document visualization: {url}')

    def _prettify_doc_dict(self, d: Dict):
        """Changes recursively a dictionary to show nd array fields as lists of values

        :param d: the dictionary to prettify
        """
        for key in _all_doc_array_keys:
            if key in d:
                value = getattr(self, key)
                if isinstance(value, np.ndarray):
                    d[key] = value.tolist()
            if 'chunks' in d:
                for chunk_doc, chunk_dict in zip(self.chunks, d['chunks']):
                    chunk_doc._prettify_doc_dict(chunk_dict)
            if 'matches' in d:
                for match_doc, match_dict in zip(self.matches, d['matches']):
                    match_doc._prettify_doc_dict(match_dict)

    def dict(self, prettify_ndarrays=False, *args, **kwargs):
        """Return the object in Python dictionary

        :param prettify_ndarrays: boolean indicating if the ndarrays need to be prettified to be shown as lists of values
        :param args: Extra positional arguments
        :param kwargs: Extra keyword arguments
        :return: dict representation of the object
        """
        d = super().dict(*args, **kwargs)
        if prettify_ndarrays:
            self._prettify_doc_dict(d)
        return d

    def json(self, prettify_ndarrays=False, *args, **kwargs):
        """Return the object in JSON string

        :param prettify_ndarrays: boolean indicating if the ndarrays need to be prettified to be shown as lists of values
        :param args: Extra positional arguments
        :param kwargs: Extra keyword arguments
        :return: JSON string of the object
        """
        if prettify_ndarrays:
            import json

            d = super().dict(*args, **kwargs)
            self._prettify_doc_dict(d)
            return json.dumps(d, sort_keys=True, **kwargs)
        else:
            return super().json(*args, **kwargs)

    @property
    def non_empty_fields(self) -> Tuple[str]:
        """Return the set fields of the current document that are not empty

        :return: the tuple of non-empty fields
        """
        return tuple(field[0].name for field in self.ListFields())

    @staticmethod
    def attributes(
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
        import inspect

        support_keys = []

        if include_proto_fields:
            support_keys = list(jina_pb2.DocumentProto().DESCRIPTOR.fields_by_name)
        if include_proto_fields_camelcase:
            support_keys += list(
                jina_pb2.DocumentProto().DESCRIPTOR.fields_by_camelcase_name
            )

        if include_properties:
            support_keys += [
                name
                for (name, value) in inspect.getmembers(
                    Document, lambda x: isinstance(x, property)
                )
            ]
        return list(set(support_keys))

    def __getattr__(self, item):
        if hasattr(self._pb_body, item):
            value = getattr(self._pb_body, item)
        else:
            value = dunder_get(self._pb_body, item)
        return value


def _is_uri(value: str) -> bool:
    scheme = urllib.parse.urlparse(value).scheme
    return (
        (scheme in {'http', 'https'})
        or (scheme in {'data'})
        or os.path.exists(value)
        or os.access(os.path.dirname(value), os.W_OK)
    )


def _is_datauri(value: str) -> bool:
    scheme = urllib.parse.urlparse(value).scheme
    return scheme in {'data'}


def _contains_conflicting_content(**kwargs):
    content_keys = 0
    for k in kwargs.keys():
        if k in _all_doc_content_keys:
            content_keys += 1
            if content_keys > 1:
                return True

    return False
