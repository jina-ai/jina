import itertools
import json
from abc import abstractmethod
from collections.abc import MutableSequence, Iterable as Itr
from contextlib import nullcontext
from typing import (
    Union,
    Iterable,
    Tuple,
    List,
    Iterator,
    TextIO,
    Optional,
    Generator,
    BinaryIO,
    TypeVar,
    Dict,
    Sequence,
)

import numpy as np

from .abstract import AbstractDocumentArray
from .neural_ops import DocumentArrayNeuralOpsMixin
from .search_ops import DocumentArraySearchOpsMixin
from .traversable import TraversableSequence
from ..document import Document
from ...helper import typename
from ...proto import jina_pb2

try:
    # when protobuf using Cpp backend
    from google.protobuf.pyext._message import (
        RepeatedCompositeContainer as RepeatedContainer,
    )
except:
    # when protobuf using Python backend
    from google.protobuf.internal.containers import (
        RepeatedCompositeFieldContainer as RepeatedContainer,
    )

__all__ = ['DocumentArray', 'DocumentArrayGetAttrMixin']

DocumentArraySourceType = TypeVar(
    'DocumentArraySourceType',
    jina_pb2.DocumentArrayProto,
    Sequence[Document],
    Sequence[jina_pb2.DocumentProto],
    Document,
)


class DocumentArrayGetAttrMixin:
    """A mixin that provides attributes getter in bulk """

    @abstractmethod
    def __iter__(self):
        ...

    @abstractmethod
    def __len__(self):
        """Any implementation needs to implement the `length` method"""
        ...

    @abstractmethod
    def __getitem__(self, item: int):
        """Any implementation needs to implement access via integer item

        :param item: the item index to access
        """
        ...

    def get_attributes(self, *fields: str) -> Union[List, List[List]]:
        """Return all nonempty values of the fields from all docs this array contains

        :param fields: Variable length argument with the name of the fields to extract
        :return: Returns a list of the values for these fields.
            When `fields` has multiple values, then it returns a list of list.
        """
        contents = [doc.get_attributes(*fields) for doc in self]

        if len(fields) > 1:
            contents = list(map(list, zip(*contents)))

        return contents

    def get_attributes_with_docs(
        self,
        *fields: str,
    ) -> Tuple[Union[List, List[List]], 'DocumentArray']:
        """Return all nonempty values of the fields together with their nonempty docs

        :param fields: Variable length argument with the name of the fields to extract
        :return: Returns a tuple. The first element is  a list of the values for these fields.
            When `fields` has multiple values, then it returns a list of list. The second element is the non-empty docs.
        """

        contents = []
        docs_pts = []

        for doc in self:
            contents.append(doc.get_attributes(*fields))
            docs_pts.append(doc)

        if len(fields) > 1:
            contents = list(map(list, zip(*contents)))

        return contents, DocumentArray(docs_pts)

    @property
    @abstractmethod
    def embeddings(self) -> np.ndarray:
        """Return a `np.ndarray` stacking all the `embedding` attributes as rows."""
        ...

    @embeddings.setter
    @abstractmethod
    def embeddings(self, emb: np.ndarray):
        """Set the embeddings of the Documents
        :param emb: the embeddings to set
        """
        ...

    @property
    def blobs(self) -> np.ndarray:
        """Return a `np.ndarray` stacking all the `blob` attributes.

        The `blob` attributes are stacked together along a newly created first
        dimension (as if you would stack using ``np.stack(X, axis=0)``).

        .. warning:: This operation assumes all blobs have the same shape and dtype.
                 All dtype and shape values are assumed to be equal to the values of the
                 first element in the DocumentArray / DocumentArrayMemmap

        .. warning:: This operation currently does not support sparse arrays.
        """
        ...

    @blobs.setter
    def blobs(self, blobs: np.ndarray):
        """Set the blobs of the Documents

        :param blobs: The blob array to set. The first axis is the "row" axis.
        """

        if len(blobs) != len(self):
            raise ValueError(
                f'the number of rows in the input ({len(blobs)}), should match the'
                f'number of Documents ({len(self)})'
            )

        for d, x in zip(self, blobs):
            d.blob = x


class DocumentArray(
    TraversableSequence,
    MutableSequence,
    DocumentArrayGetAttrMixin,
    DocumentArrayNeuralOpsMixin,
    DocumentArraySearchOpsMixin,
    Itr,
    AbstractDocumentArray,
):
    """
    :class:`DocumentArray` is a mutable sequence of :class:`Document`.
    It gives an efficient view of a list of Document. One can iterate over it like
    a generator but ALSO modify it, count it, get item, or union two 'DocumentArray's using the '+' and '+=' operators.

    It is supposed to act as a view containing a pointer to a `RepeatedContainer` of `DocumentProto` while offering `Document` Jina native types
    when getting items or iterating over it

    :param docs: the document array to construct from. One can also give `DocumentArrayProto` directly, then depending on the ``copy``,
                it builds a view or a copy from it. It also can accept a List
    """

    def __init__(self, docs: Optional[DocumentArraySourceType] = None):
        super().__init__()
        self._pb_body = []
        if docs is not None:
            if isinstance(docs, jina_pb2.DocumentArrayProto):
                # This would happen when loading from file or memmap
                self._pb_body = docs.docs
            elif isinstance(docs, RepeatedContainer):
                # This would happen when `doc.matches` or `doc.chunks`
                self._pb_body = docs
            elif isinstance(docs, DocumentArray):
                # This would happen in the client
                self._pb_body = docs._pb_body
            else:
                if isinstance(docs, Document):
                    # single Document
                    docs = [docs]

                from .memmap import DocumentArrayMemmap

                if isinstance(
                    docs, (list, tuple, Generator, DocumentArrayMemmap, itertools.chain)
                ):
                    # This would happen in the client
                    for doc in docs:
                        if isinstance(doc, Document):
                            self._pb_body.append(doc.proto)
                        elif isinstance(doc, jina_pb2.DocumentProto):
                            self._pb_body.append(doc)
                        else:
                            raise ValueError(f'Unexpected element in an input list')
                else:
                    raise ValueError(
                        f'DocumentArray got an unexpected input {type(docs)}'
                    )
        self._update_id_to_index_map()

    def _update_id_to_index_map(self):
        """Update the id_to_index map by enumerating all Documents in self._pb_body.

        Very costy! Only use this function when self._pb_body is dramtically changed.
        """

        self._id_to_index = {
            d.id: i for i, d in enumerate(self._pb_body)
        }  # type: Dict[str, int]

    def insert(self, index: int, doc: 'Document') -> None:
        """
        Insert :param:`doc.proto` at :param:`index` into the list of `:class:`DocumentArray` .

        :param index: Position of the insertion.
        :param doc: The doc needs to be inserted.
        """
        self._pb_body.insert(index, doc.proto)
        self._id_to_index[doc.id] = index

    def __setitem__(self, key, value: 'Document'):
        if isinstance(key, int):
            self[key].CopyFrom(value)
            self._id_to_index[value.id] = key
        elif isinstance(key, str):
            self[self._id_to_index[key]].CopyFrom(value)
        else:
            raise IndexError(f'do not support this index {key}')

    def __delitem__(self, index: Union[int, str, slice]):
        if isinstance(index, int):
            del self._pb_body[index]
        elif isinstance(index, str):
            del self[self._id_to_index[index]]
            self._id_to_index.pop(index)
        elif isinstance(index, slice):
            del self._pb_body[index]
        else:
            raise IndexError(
                f'do not support this index type {typename(index)}: {index}'
            )

    def __eq__(self, other):
        return (
            type(self._pb_body) is type(other._pb_body)
            and self._pb_body == other._pb_body
        )

    def __len__(self):
        return len(self._pb_body)

    def __iter__(self) -> Iterator['Document']:
        for d in self._pb_body:
            yield Document(d)

    def __contains__(self, item: str):
        return item in self._id_to_index

    def __getitem__(self, item: Union[int, str, slice]):
        if isinstance(item, int):
            return Document(self._pb_body[item])
        elif isinstance(item, str):
            return self[self._id_to_index[item]]
        elif isinstance(item, slice):
            return DocumentArray(self._pb_body[item])
        else:
            raise IndexError(f'do not support this index type {typename(item)}: {item}')

    def __add__(self, other: Iterable['Document']):
        v = DocumentArray()
        for doc in self:
            v.append(doc)
        for doc in other:
            v.append(doc)
        return v

    def __iadd__(self, other: Iterable['Document']):
        for doc in other:
            self.append(doc)
        return self

    def append(self, doc: 'Document'):
        """
        Append :param:`doc` in :class:`DocumentArray`.

        :param doc: The doc needs to be appended.
        """
        self._id_to_index[doc.id] = len(self._pb_body)
        self._pb_body.append(doc.proto)

    def extend(self, iterable: Iterable['Document']) -> None:
        """
        Extend the :class:`DocumentArray` by appending all the items from the iterable.

        :param iterable: the iterable of Documents to extend this array with
        """
        if not iterable:
            return

        for doc in iterable:
            self.append(doc)

    def clear(self):
        """Clear the data of :class:`DocumentArray`"""
        del self._pb_body[:]
        self._id_to_index.clear()

    def reverse(self):
        """In-place reverse the sequence."""
        size = len(self._pb_body)
        hi_idx = size - 1
        for i in range(int(size / 2)):
            tmp = jina_pb2.DocumentProto()
            tmp.CopyFrom(self._pb_body[hi_idx])
            self._pb_body[hi_idx].CopyFrom(self._pb_body[i])
            self._pb_body[i].CopyFrom(tmp)
            hi_idx -= 1
        self._update_id_to_index_map()

    def sort(self, key=None, *args, **kwargs):
        """
        Sort the items of the :class:`DocumentArray` in place.

        :param key: key callable to sort based upon
        :param args: variable set of arguments to pass to the sorting underlying function
        :param kwargs: keyword arguments to pass to the sorting underlying function
        """
        if key:

            def overriden_key(proto):
                # Function to override the `proto` and wrap it around a `Document` to enable sorting via
                # `Document-like` interface
                d = Document(proto)
                return key(d)

            # Logic here: `overriden_key` is offered to allow the user sort via pythonic `Document` syntax. However,
            # maybe there may be cases where this won't work and the user may enter `proto-like` interface. To make
            # sure (quite fragile) the `sort` will work seamlessly, it tries to apply `key` to the first element and
            # see if it works. If it works it can sort with `proto` interface, otherwise use `Document` interface one.
            # (Very often the 2 interfaces are both the same and valid, so proto will have less overhead
            overriden = False
            try:
                key(self._pb_body[0])
            except:
                overriden = True

            if not overriden:
                self._pb_body.sort(key=key, *args, **kwargs)
            else:
                self._pb_body.sort(key=overriden_key, *args, **kwargs)
        else:
            self._pb_body.sort(*args, **kwargs)

        self._update_id_to_index_map()

    def __bool__(self):
        """To simulate ```l = []; if l: ...```

        :return: returns true if the length of the array is larger than 0
        """
        return len(self) > 0

    def __str__(self):

        content = f'{self.__class__.__name__} has {len(self._pb_body)} items'

        if len(self._pb_body) > 3:
            content += ' (showing first three)'

        content += ':\n'
        content += ',\n'.join(str(Document(d)) for d in self._pb_body[:3])

        return content

    def __repr__(self):
        content = ' '.join(
            f'{k}={v}' for k, v in {'length': len(self._pb_body)}.items()
        )
        content += f' at {id(self)}'
        content = content.strip()
        return f'<{typename(self)} {content}>'

    def save(
        self, file: Union[str, TextIO, BinaryIO], file_format: str = 'json'
    ) -> None:
        """Save array elements into a JSON or a binary file.

        :param file: File or filename to which the data is saved.
        :param file_format: `json` or `binary`. JSON file is human-readable,
            but binary format gives much smaller size and faster save/load speed.
        """
        if file_format == 'json':
            self.save_json(file)
        elif file_format == 'binary':
            self.save_binary(file)
        else:
            raise ValueError('`format` must be one of [`json`, `binary`]')

    @classmethod
    def load(
        cls, file: Union[str, TextIO, BinaryIO], file_format: str = 'json'
    ) -> 'DocumentArray':
        """Load array elements from a JSON or a binary file.

        :param file: File or filename to which the data is saved.
        :param file_format: `json` or `binary`. JSON file is human-readable,
            but binary format gives much smaller size and faster save/load speed.

        :return: the loaded DocumentArray object
        """
        if file_format == 'json':
            return cls.load_json(file)
        elif file_format == 'binary':
            return cls.load_binary(file)
        else:
            raise ValueError('`format` must be one of [`json`, `binary`]')

    def save_binary(self, file: Union[str, BinaryIO]) -> None:
        """Save array elements into a binary file.

        Comparing to :meth:`save_json`, it is faster and the file is smaller, but not human-readable.

        :param file: File or filename to which the data is saved.
        """
        if hasattr(file, 'write'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file, 'wb')

        with file_ctx as fp:
            dap = jina_pb2.DocumentArrayProto()
            if self._pb_body:
                dap.docs.extend(self._pb_body)
            fp.write(dap.SerializePartialToString())

    def save_json(self, file: Union[str, TextIO]) -> None:
        """Save array elements into a JSON file.

        Comparing to :meth:`save_binary`, it is human-readable but slower to save/load and the file size larger.

        :param file: File or filename to which the data is saved.
        """
        if hasattr(file, 'write'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file, 'w')

        with file_ctx as fp:
            for d in self:
                json.dump(d.dict(), fp)
                fp.write('\n')

    @classmethod
    def load_json(cls, file: Union[str, TextIO]) -> 'DocumentArray':
        """Load array elements from a JSON file.

        :param file: File or filename to which the data is saved.

        :return: a DocumentArray object
        """

        if hasattr(file, 'read'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file)

        with file_ctx as fp:
            da = DocumentArray()
            for v in fp:
                da.append(Document(v))
            return da

    @classmethod
    def load_binary(cls, file: Union[str, BinaryIO]) -> 'DocumentArray':
        """Load array elements from a binary file.

        :param file: File or filename to which the data is saved.

        :return: a DocumentArray object
        """

        if hasattr(file, 'read'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file, 'rb')

        dap = jina_pb2.DocumentArrayProto()

        with file_ctx as fp:
            dap.ParseFromString(fp.read())
            da = DocumentArray(dap.docs)
            return da

    # Properties for fast access of commonly used attributes
    @property
    def embeddings(self) -> np.ndarray:
        """Return a `np.ndarray` stacking all the `embedding` attributes as rows.

        .. warning:: This operation assumes all embeddings have the same shape and dtype.
                 All dtype and shape values are assumed to be equal to the values of the
                 first element in the DocumentArray / DocumentArrayMemmap

        .. warning:: This operation currently does not support sparse arrays.

        :return: embeddings stacked per row as `np.ndarray`.
        """
        x_mat = b''.join(d.embedding.dense.buffer for d in self._pb_body)
        proto = self[0].proto.embedding.dense

        return np.frombuffer(x_mat, dtype=proto.dtype).reshape(
            (len(self), proto.shape[0])
        )

    @embeddings.setter
    def embeddings(self, emb: np.ndarray):
        """Set the embeddings of the Documents

        :param emb: The embedding matrix to set
        """

        if len(emb) != len(self):
            raise ValueError(
                f'the number of rows in the input ({len(emb)}), should match the'
                f'number of Documents ({len(self)})'
            )

        for d, x in zip(self, emb):
            d.embedding = x

    @DocumentArrayGetAttrMixin.blobs.getter
    def blobs(self) -> np.ndarray:
        """Return a `np.ndarray` stacking all the `blob` attributes.

        The `blob` attributes are stacked together along a newly created first
        dimension (as if you would stack using ``np.stack(X, axis=0)``).

        .. warning:: This operation assumes all blobs have the same shape and dtype.
                 All dtype and shape values are assumed to be equal to the values of the
                 first element in the DocumentArray / DocumentArrayMemmap

        .. warning:: This operation currently does not support sparse arrays.

        :return: blobs stacked per row as `np.ndarray`.
        """
        x_mat = b''.join(d.blob.dense.buffer for d in self._pb_body)
        proto = self[0].proto.blob.dense

        return np.frombuffer(x_mat, dtype=proto.dtype).reshape(
            (len(self), *proto.shape)
        )

    @staticmethod
    def _flatten(sequence) -> 'DocumentArray':
        return DocumentArray(list(itertools.chain.from_iterable(sequence)))
