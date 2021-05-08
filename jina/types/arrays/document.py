import json
from collections.abc import MutableSequence, Iterable as Itr
from contextlib import nullcontext
from typing import Union, Iterable, Tuple, List, Iterator, TextIO

from .traversable import TraversableSequence
from ...enums import EmbeddingClsType
from ...helper import typename, cached_property
from ...logging import default_logger
from ...proto.jina_pb2 import DocumentProto

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

__all__ = ['DocumentArray']

if False:
    from ..document import Document
    from scipy.sparse import coo_matrix
    from scipy.sparse import coo_matrix

    # fix type-hint complain for sphinx and flake
    from typing import TypeVar
    import numpy as np
    import scipy
    import tensorflow as tf
    import torch

    EmbeddingType = TypeVar(
        'EncodingType',
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


class DocumentArray(TraversableSequence, MutableSequence, Itr):
    """
    :class:`DocumentArray` is a mutable sequence of :class:`Document`.
    It gives an efficient view of a list of Document. One can iterate over it like
    a generator but ALSO modify it, count it, get item, or union two 'DocumentArray's using the '+' and '+=' operators.

    :param docs_proto: A list of :class:`Document`
    :type docs_proto: Union['RepeatedContainer', Sequence['Document']]
    """

    def __init__(
            self, docs_proto: Union['RepeatedContainer', Iterable['Document'], None] = None
    ):
        super().__init__()
        if docs_proto is not None:
            self._docs_proto = docs_proto
        else:
            self._docs_proto = []

    def insert(self, index: int, doc: 'Document') -> None:
        """
        Insert :param:`doc.proto` at :param:`index` into the list of `:class:`DocumentArray` .

        :param index: Position of the insertion.
        :param doc: The doc needs to be inserted.
        """
        self._docs_proto.insert(index, doc.proto)

    def __setitem__(self, key, value: 'Document'):
        if isinstance(key, (int, str)):
            self[key].CopyFrom(value)
        else:
            raise IndexError(f'do not support this index {key}')

    def __delitem__(self, index: Union[int, str, slice]):
        if isinstance(index, int):
            del self._docs_proto[index]
        elif isinstance(index, str):
            del self._docs_map[index]
        elif isinstance(index, slice):
            del self._docs_proto[index]
        else:
            raise IndexError(f'do not support this index type {typename(index)}: {index}')

    def __eq__(self, other):
        return type(self._docs_proto) is type(other._docs_proto) and self._docs_proto == other._docs_proto

    def __len__(self):
        return len(self._docs_proto)

    def __iter__(self) -> Iterator['Document']:
        from ..document import Document

        for d in self._docs_proto:
            yield Document(d)

    def __getitem__(self, item: Union[int, str, slice]):
        from ..document import Document

        if isinstance(item, int):
            return Document(self._docs_proto[item])
        elif isinstance(item, str):
            return Document(self._docs_map[item])
        elif isinstance(item, slice):
            return DocumentArray(self._docs_proto[item])
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
        self._docs_proto.append(doc.proto)

    def extend(self, iterable: Iterable['Document']) -> None:
        """
        Extend the :class:`DocumentArray` by appending all the items from the iterable.

        :param iterable: the iterable of Documents to extend this array with
        """
        for doc in iterable:
            self.append(doc)

    def clear(self):
        """Clear the data of :class:`DocumentArray`"""
        del self._docs_proto[:]

    def reverse(self):
        """In-place reverse the sequence."""
        if isinstance(self._docs_proto, RepeatedContainer):
            size = len(self._docs_proto)
            hi_idx = size - 1
            for i in range(int(size / 2)):
                tmp = DocumentProto()
                tmp.CopyFrom(self._docs_proto[hi_idx])
                self._docs_proto[hi_idx].CopyFrom(self._docs_proto[i])
                self._docs_proto[i].CopyFrom(tmp)
                hi_idx -= 1
        elif isinstance(self._docs_proto, list):
            self._docs_proto.reverse()

    @cached_property
    def _docs_map(self):
        """Build a doc_id to doc mapping so one can later index a Document using doc_id as string key."""
        return {d.id: d for d in self._docs_proto}

    def sort(self, *args, **kwargs):
        """
        Sort the items of the :class:`DocumentArray` in place.

        :param args: variable set of arguments to pass to the sorting underlying function
        :param kwargs: keyword arguments to pass to the sorting underlying function
        """
        self._docs_proto.sort(*args, **kwargs)

    def get_all_sparse_embeddings(
            self, embedding_cls_type: EmbeddingClsType
    ) -> Tuple['SparseEmbeddingType', 'DocumentArray']:
        """Return all embeddings from every document in this array as a sparse array

        :param embedding_cls_type: Type of sparse matrix backend, e.g. `scipy`, `torch` or `tf`.

        :return: The corresponding documents in a :class:`DocumentArray`,
            and the documents have no embedding in a :class:`DocumentArray`.
        :rtype: A tuple of embedding and DocumentArray as sparse arrays
        """

        def stack_embeddings(embeddings):
            if embedding_cls_type.is_scipy:
                import scipy

                return scipy.sparse.vstack(embeddings)
            elif embedding_cls_type.is_torch:
                import torch

                return torch.vstack(embeddings)
            elif embedding_cls_type.is_tf:
                return embeddings
            else:
                raise ValueError(
                    f'Trying to stack sparse embeddings with embedding_cls_type {embedding_cls_type} failed'
                )

        def get_sparse_ndarray_type_kwargs():
            if embedding_cls_type.is_scipy:
                from jina.types.ndarray.sparse.scipy import SparseNdArray

                if not embedding_cls_type.is_scipy_stackable not in ['coo', 'csr']:
                    default_logger.warning(
                        f'found `{embedding_cls_type.name}` matrix, recommend to use `coo` or `csr` type.'
                    )
                return SparseNdArray, {'sp_format': embedding_cls_type.scipy_cls_type}
            elif embedding_cls_type.is_torch:
                from jina.types.ndarray.sparse.pytorch import SparseNdArray

                return SparseNdArray, {}
            elif embedding_cls_type.is_tf:
                from jina.types.ndarray.sparse.tensorflow import SparseNdArray

                return SparseNdArray, {}
            else:
                raise ValueError(
                    f'Trying to get sparse embeddings with embedding_cls_type {embedding_cls_type} failed'
                )

        embeddings = []
        docs_pts = []
        bad_docs = []
        sparse_ndarray_type, sparse_kwargs = get_sparse_ndarray_type_kwargs()
        for doc in self:
            embedding = doc.get_sparse_embedding(
                sparse_ndarray_cls_type=sparse_ndarray_type, **sparse_kwargs
            )
            if embedding is None:
                bad_docs.append(doc)
                continue
            embeddings.append(embedding)
            docs_pts.append(doc)

        if bad_docs:
            default_logger.warning(
                f'found {len(bad_docs)} docs at granularity {bad_docs[0].granularity} are missing sparse_embedding'
            )

        return stack_embeddings(embeddings), docs_pts

    def get_attributes(self, *fields: str) -> Union[List, List[List]]:
        """Return all nonempty values of the fields from all docs this array contains

        :param fields: Variable length argument with the name of the fields to extract
        :return: Returns a list of the values for these fields.
            When `fields` has multiple values, then it returns a list of list.
        """
        return self.get_attributes_with_docs(*fields)[0]

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
        bad_docs = []

        for doc in self:
            r = doc.get_attributes(*fields)
            if r is None:
                bad_docs.append(doc)
                continue
            contents.append(r)
            docs_pts.append(doc)

        if len(fields) > 1:
            contents = list(map(list, zip(*contents)))

        if bad_docs:
            default_logger.warning(
                f'found {len(bad_docs)} docs at granularity {bad_docs[0].granularity} are missing one of the '
                f'following fields: {fields} '
            )

        if not docs_pts:
            default_logger.warning('no documents are extracted')

        return contents, DocumentArray(docs_pts)

    def __bool__(self):
        """To simulate ```l = []; if l: ...```

        :return: returns true if the length of the array is larger than 0
        """
        return len(self) > 0

    def __str__(self):
        from ..document import Document

        content = f'in total {len(self._docs_proto)} items\n' if len(self._docs_proto) > 3 else ''
        content += ',\n'.join(str(Document(d)) for d in self._docs_proto[:3])

        return content

    def __repr__(self):
        content = ' '.join(
            f'{k}={v}' for k, v in {'length': len(self._docs_proto)}.items()
        )
        content += f' at {id(self)}'
        content = content.strip()
        return f'<{typename(self)} {content}>'

    def save(self, file: Union[str, TextIO]) -> None:
        """Save array elements into a JSON file.

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

    @staticmethod
    def load(file: Union[str, TextIO]) -> 'DocumentArray':
        """Load array elements from a JSON file.

        :param file: File or filename to which the data is saved.
        """

        if hasattr(file, 'read'):
            file_ctx = nullcontext(file)
        else:
            file_ctx = open(file)

        from jina import Document
        da = DocumentArray()
        with file_ctx as fp:
            for v in fp:
                da.append(Document(v))
        return da