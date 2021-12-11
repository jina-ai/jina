import json
import mimetypes
import uuid
from typing import (
    Dict,
    Iterable,
    Optional,
    TypeVar,
    Union,
    overload,
    TYPE_CHECKING,
    Tuple,
    Sequence,
)

import numpy as np
from google.protobuf import json_format

from .mixins import AllMixins
from .mixins.version import versioned

from ..base import BaseProtoView
from ..helper import typename
from ..ndarray import NdArray
from ..proto.docarray_pb2 import DocumentProto
from ..simple import StructView, NamedScoreMap

if TYPE_CHECKING:
    from ..ndarray import ArrayType
    from ..simple import NamedScore
    from ..array.chunk import ChunkArray
    from ..array.match import MatchArray

    DocumentSourceType = TypeVar('DocumentSourceType', bytes, str, Dict)


_all_mime_types = set(mimetypes.types_map.values())
_all_doc_content_keys = {'content', 'blob', 'text', 'buffer'}


class Document(AllMixins, BaseProtoView):
    """
    :class:`Document` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.docarray_pb2.DocumentProto` object without working with Protobuf itself.

    To create a :class:`Document` object, simply:

        .. highlight:: python
        .. code-block:: python

            from jina import Document
            d = Document()
            d.text = 'abc'

    Jina requires each Document to have a string id. You can set a custom one,
    or if non has been set a random one will be assigned.

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
    from ``docarray_pb2.DocumentProto``, ``bytes``, ``str``, and ``Dict``. You can also use it as view (i.e.
    weak reference when building from an existing ``docarray_pb2.DocumentProto``). For example,

        .. highlight:: python
        .. code-block:: python

            a = DocumentProto()
            b = Document(a, copy=False)
            a.text = 'hello'
            assert b.text == 'hello'

    You can leverage the :meth:`convert_a_to_b` interface to convert between content forms.

    """

    # overload_inject_start_document
    @overload
    def __init__(
        self,
        adjacency: Optional[int] = None,
        blob: Optional['ArrayType'] = None,
        buffer: Optional[bytes] = None,
        chunks: Optional[Iterable['Document']] = None,
        embedding: Optional['ArrayType'] = None,
        granularity: Optional[int] = None,
        id: Optional[str] = None,
        location: Optional[Sequence[float]] = None,
        matches: Optional[Iterable['Document']] = None,
        mime_type: Optional[str] = None,
        modality: Optional[str] = None,
        offset: Optional[float] = None,
        parent_id: Optional[str] = None,
        tags: Optional[Union[Dict, StructView]] = None,
        text: Optional[str] = None,
        uri: Optional[str] = None,
        weight: Optional[float] = None,
        **kwargs,
    ):
        """
        :param adjacency: the adjacency of this Document
        :param blob: the blob content of thi Document
        :param buffer: the buffer bytes from this document
        :param chunks: the array of chunks of this document
        :param embedding: the embedding of this Document
        :param granularity: the granularity of this Document
        :param id: the id of this Document
        :param location: location info in a tuple.
        :param matches: the array of matches attached to this document
        :param mime_type: the mime_type of this Document
        :param modality: the modality of the document.
        :param offset: the offset
        :param parent_id: the parent id of this Document
        :param tags: a Python dict view of the tags.
        :param text: the text from this document content
        :param uri: the uri of this Document
        :param weight: the weight of the document
        :param kwargs: other parameters to be set _after_ the document is constructed
        """

    # overload_inject_end_document

    _PbMsg = DocumentProto

    def __init__(
        self,
        obj: Optional[Union['DocumentSourceType', 'Document']] = None,
        field_resolver: Dict[str, str] = None,
        copy: bool = False,
        **kwargs,
    ):
        """
        :param obj: the document to construct from. If ``bytes`` is given
                then deserialize a :class:`DocumentProto`; ``dict`` is given then
                parse a :class:`DocumentProto` from it; ``str`` is given, then consider
                it as a JSON string and parse a :class:`DocumentProto` from it; finally,
                one can also give `DocumentProto` directly, then depending on the ``copy``,
                it builds a view or a copy from it.
        :param copy: when ``document`` is given as a :class:`DocumentProto` object, build a
                view (i.e. weak reference) from it or a deep copy from it.
        :param field_resolver: a map from field names defined in JSON, dict to the field
            names defined in Document.
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
        try:
            super().__init__(obj, copy=copy)

            if self._pb_body is None and isinstance(obj, (dict, str)):
                # note that not any dict can be parsed in this branch. As later we use Protobuf JSON parser, this
                # dict must be a valid JSON. The next lines make sure the dict is a valid json.
                if isinstance(obj, dict):
                    try:
                        json.dumps(obj)
                    except:
                        raise json_format.ParseError

                if isinstance(obj, str):
                    obj = json.loads(obj)

                if field_resolver:
                    obj = {field_resolver.get(k, k): v for k, v in obj.items()}

                user_fields = set(obj)
                support_fields = set(
                    self.attributes(
                        include_proto_fields_camelcase=True,
                        include_properties=False,
                    )
                )

                self._pb_body = self._PbMsg()
                if support_fields.issuperset(user_fields):
                    json_format.ParseDict(obj, self._pb_body)
                else:
                    _intersect = support_fields.intersection(user_fields)
                    _remainder = user_fields.difference(_intersect)
                    if _intersect:
                        json_format.ParseDict(
                            {k: obj[k] for k in _intersect}, self._pb_body
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
                            self._set_attributes(**{p: obj[p] for p in _intersect2})

                        if _remainder2:
                            self._pb_body.tags.update({k: obj[k] for k in _remainder})

            if self._pb_body is None and obj is not None:
                raise ValueError
        except json_format.ParseError:
            # append everything to kwargs that is more powerful in setting attributes
            self._pb_body = self._PbMsg()
            if isinstance(obj, dict):
                kwargs.update(obj)
        except Exception as ex:
            raise ValueError(f'Fail to construct Document from {obj!r}') from ex

        if self._pb_body.id is None or not self._pb_body.id:
            self.id = uuid.uuid1().hex

        if kwargs:
            # check if there are mutually exclusive content fields
            if len(_all_doc_content_keys.intersection(kwargs.keys())) > 1:
                raise ValueError(
                    f'Document content fields are mutually exclusive, please provide only one of {_all_doc_content_keys}'
                )
            self._set_attributes(**kwargs)

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
        if value is None:
            self.pop('weight')
            return
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
        if value is None:
            self.pop('modality')
            return
        self._pb_body.modality = value

    @property
    def tags(self) -> StructView:
        """Return the `tags` field of this Document as a Python dict

        :return: a Python dict view of the tags.
        """
        return StructView(self._pb_body.tags)

    @tags.setter
    def tags(self, value: Union[Dict, StructView]):
        """Set the `tags` field of this Document to a Python dict

        :param value: a Python dict or a StructView
        """
        if value is None:
            self.pop('tags')
            return

        if isinstance(value, StructView):
            self._pb_body.tags.Clear()
            self._pb_body.tags.update(value._pb_body)
        elif isinstance(value, dict):
            self._pb_body.tags.Clear()
            self._pb_body.tags.update(value)
        else:
            raise TypeError(f'{typename(value)} {value!r} is not supported.')

    @property
    def id(self) -> str:
        """The document id in string.

        :return: the id of this Document
        """
        return self._pb_body.id

    @property
    def parent_id(self) -> str:
        """The document's parent id in string.

        :return: the parent id of this Document
        """
        return self._pb_body.parent_id

    @id.setter
    def id(self, value: str):
        """Set document id to a string value.

        :param value: id as string
        """
        if value is None:
            self.pop('id')
            return
        self._pb_body.id = str(value)

    @parent_id.setter
    def parent_id(self, value: str):
        """Set document's parent id to a string value.

        :param value: id as string
        """
        if value is None:
            self.pop('parent_id')
            return
        self._pb_body.parent_id = str(value)

    @property
    def blob(self) -> 'ArrayType':
        """Return ``blob``, one of the content form of a Document.

        .. note::
            Use :attr:`content` to return the content of a Document

            This property will return the `blob` of the `Document` as a `Dense` or `Sparse` array depending on the actual
            proto instance stored. In the case where the `blob` stored is sparse, it will return them as a `coo` matrix.

        :return: the blob content of thi Document
        """
        return NdArray(self._pb_body.blob).value

    @blob.setter
    def blob(self, value: 'ArrayType'):
        """Set the `blob` to `value`.

        :param value: the array value to set the blob
        """
        if value is None:
            self.pop('blob')
            return
        NdArray(self._pb_body.blob).value = value

    @property
    def embedding(self) -> 'ArrayType':
        """Return ``embedding`` of the content of a Document.

         .. note::
            This property will return the `embedding` of the `Document` as a `Dense` or `Sparse` array depending on the actual
            proto instance stored. In the case where the `embedding` stored is sparse, it will return them as a `coo` matrix.

        :return: the embedding of this Document
        """
        return NdArray(self._pb_body.embedding).value

    @embedding.setter
    def embedding(self, value: 'ArrayType'):
        """Set the ``embedding`` of the content of a Document.

        :param value: the array value to set the embedding
        """
        if value is None:
            self.pop('embedding')
            return
        NdArray(self._pb_body.embedding).value = value

    @property
    @versioned
    def matches(self) -> 'MatchArray':
        """Get all matches of the current document.

        :return: the array of matches attached to this document
        """
        # Problem with cyclic dependency
        from ..array.match import MatchArray

        return MatchArray(self._pb_body.matches, reference_doc=self)

    @matches.setter
    def matches(self, value: Iterable['Document']):
        """Get all chunks of the current document.

        :param value: value to set
        """
        if value is None:
            self.pop('matches')
            return
        self.pop('matches')
        self.matches.extend(value)

    @property
    @versioned
    def chunks(self) -> 'ChunkArray':
        """Get all chunks of the current document.

        :return: the array of chunks of this document
        """
        # Problem with cyclic dependency
        from ..array.chunk import ChunkArray

        return ChunkArray(self._pb_body.chunks, reference_doc=self)

    @chunks.setter
    def chunks(self, value: Iterable['Document']):
        """Get all chunks of the current document.

        :param value: the array of chunks of this document
        """
        if value is None:
            self.pop('chunks')
            return
        self.pop('chunks')
        self.chunks.extend(value)

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
        """Set the ``buffer`` to `value`.

        :param value: the bytes value to set the buffer
        """
        if value is None:
            self.pop('buffer')
            return
        self._pb_body.buffer = value

    @property
    def text(self) -> str:
        """Return ``text``, one of the content form of a Document.

        .. note::
            Use :attr:`content` to return the content of a Document

        :return: the text from this document content
        """
        return self._pb_body.text

    @text.setter
    def text(self, value: str):
        """Set the `text` to `value`

        :param value: the text value to set as content
        """
        if value is None:
            self.pop('text')
            self.mime_type = None
            return
        self._pb_body.text = value
        self.mime_type = 'text/plain'

    @property
    def uri(self) -> str:
        """Return the URI of the document.

        :return: the uri of this Document
        """
        return self._pb_body.uri

    @uri.setter
    def uri(self, value: str):
        """Set the URI of the document.

        .. note::
            :attr:`mime_type` will be updated accordingly

        :param value: acceptable URI/URL, raise ``ValueError`` when it is not a valid URI
        """
        if value is None:
            self.pop('uri')
            self.mime_type = None
            return
        self._pb_body.uri = value
        mime_type = mimetypes.guess_type(value)[0]
        if mime_type:
            self.mime_type = mime_type  # Remote http/https contents mime_type will not be recognized.

    @property
    def mime_type(self) -> str:
        """Get MIME type of the document

        :return: the mime_type of this Document
        """
        return self._pb_body.mime_type

    @mime_type.setter
    def mime_type(self, value: str):
        """Set MIME type of the document

        :param value: the acceptable MIME type, raise ``ValueError`` when MIME type is not
                recognizable.
        """
        if value is None:
            self.pop('mime_type')
            return
        if value in _all_mime_types:
            self._pb_body.mime_type = value
        elif value:
            # given but not recognizable, do best guess
            r = mimetypes.guess_type(f'*.{value}')[0]
            if r:
                self._pb_body.mime_type = r
            else:
                self._pb_body.mime_type = value

    @property
    def granularity(self) -> int:
        """Return the granularity of the document.

        :return: the granularity of this Document
        """
        return self._pb_body.granularity

    @granularity.setter
    def granularity(self, value: int):
        """Set the granularity of the document.

        :param value: the value of the granularity to be set
        """
        if value is None:
            self.pop('granularity')
            return
        self._pb_body.granularity = value

    @property
    def adjacency(self) -> int:
        """Return the adjacency of the document.

        :return: the adjacency of this Document
        """
        return self._pb_body.adjacency

    @adjacency.setter
    def adjacency(self, value: int):
        """Set the adjacency of the document.

        :param value: the value of the adjacency to be set
        """
        if value is None:
            self.pop('adjacency')
            return
        self._pb_body.adjacency = value

    @property
    def scores(self):
        """Return the scores of the document.

        :return: the scores attached to this document as `:class:NamedScoreMapping`
        """
        return NamedScoreMap(self._pb_body.scores)

    @scores.setter
    def scores(
        self,
        value: Dict[str, Union['NamedScore', float, np.generic]],
    ):
        """Sets the scores of the `Document`. Specially important to provide the ability to start `scores` as:

            .. highlight:: python
            .. code-block:: python

                from jina import Document
                from jina.types.score import NamedScore
                d = Document(scores={'euclidean': 5, 'cosine': NamedScore(value=0.5)})

        :param value: the dictionary to set the scores
        """
        if value is None:
            self.pop('scores')
            return

        scores = NamedScoreMap(self._pb_body.scores)
        for k, v in value.items():
            scores[k] = v

    @property
    def evaluations(self) -> NamedScoreMap:
        """Return the evaluations of the document.

        :return: the evaluations attached to this document as `:class:NamedScoreMapping`
        """
        return NamedScoreMap(self._pb_body.evaluations)

    @evaluations.setter
    def evaluations(
        self,
        value: Dict[str, Union['NamedScore', float, np.generic]],
    ):
        """Sets the evaluations of the `Document`. Specially important to provide the ability to start `evaluations` as:

            .. highlight:: python
            .. code-block:: python

                from jina import Document
                from jina.types.score import NamedScore
                d = Document(evaluations={'precision': 0.9, 'recall': NamedScore(value=0.5)})

        :param value: the dictionary to set the evaluations
        """
        if value is None:
            self.pop('evaluations')
            return
        scores = NamedScoreMap(self._pb_body.evaluations)
        for k, v in value.items():
            scores[k] = v

    @property
    def location(self) -> Tuple[float]:
        """Get the location information.

        :return: location info in a tuple.
        """
        return tuple(self._pb_body.location)

    @location.setter
    def location(self, value: Sequence[float]):
        """Set the location information of this Document.

        Location could mean the start and end index of a string;
        could be x,y (top, left) coordinate of an image crop; could be timestamp of an audio clip.

        :param value: the location info to be set.
        """
        if value is None:
            self.pop('location')
            return
        self.pop('location')
        self._pb_body.location.extend(value)

    @property
    def offset(self) -> float:
        """Get the offset information of this Document.

        :return: the offset
        """
        return self._pb_body.offset

    @offset.setter
    def offset(self, value: float):
        """Set the offset of this Document

        :param value: the offset value to be set.
        """
        if value is None:
            self.pop('offset')

        self._pb_body.offset = value
