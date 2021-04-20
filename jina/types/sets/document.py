from collections.abc import MutableSequence
from typing import Union, Iterable, Tuple, Sequence, List, Optional

import numpy as np

from ...helper import typename
from ...logging import default_logger
from ...enums import EmbeddingClsType

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

from ...proto.jina_pb2 import DocumentProto
from .traversable import TraversableSequence

__all__ = ['DocumentSet']

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


class DocumentSet(TraversableSequence, MutableSequence):
    """
    :class:`DocumentSet` is a mutable sequence of :class:`Document`.
    It gives an efficient view of a list of Document. One can iterate over it like
    a generator but ALSO modify it, count it, get item, or union two 'DocumentSet's using the '+' and '+=' operators.

    :param docs_proto: A list of :class:`Document`
    :type docs_proto: Union['RepeatedContainer', Sequence['Document']]
    """

    def __init__(self, docs_proto: Union['RepeatedContainer', Sequence['Document']]):
        super().__init__()
        self._docs_proto = docs_proto
        self._docs_map = {}

    def insert(self, index: int, doc: 'Document') -> None:
        """
        Insert :param:`doc.proto` at :param:`index` into the list of `:class:`DocumentSet` .

        :param index: Position of the insertion.
        :param doc: The doc needs to be inserted.
        """
        self._docs_proto.insert(index, doc.proto)

    def __setitem__(self, key, value: 'Document'):
        if isinstance(key, int):
            self._docs_proto[key].CopyFrom(value)
        elif isinstance(key, str):
            self._docs_map[key].CopyFrom(value)
        else:
            raise IndexError(f'do not support this index {key}')

    def __delitem__(self, index):
        del self._docs_proto[index]

    def __len__(self):
        return len(self._docs_proto)

    def __iter__(self) -> 'Document':
        from ..document import Document

        for d in self._docs_proto:
            yield Document(d)

    def __getitem__(self, item):
        from ..document import Document

        if isinstance(item, int):
            return Document(self._docs_proto[item])
        elif isinstance(item, str):
            return Document(self._docs_map[item])
        elif isinstance(item, slice):
            return DocumentSet(self._docs_proto[item])
        else:
            raise IndexError(f'do not support this index {item}')

    def __add__(self, other: 'DocumentSet'):
        v = DocumentSet([])
        for doc in self:
            v.add(doc)
        for doc in other:
            v.add(doc)
        return v

    def __iadd__(self, other: 'DocumentSet'):
        for doc in other:
            self.add(doc)
        return self

    def append(self, doc: 'Document') -> 'Document':
        """
        Append :param:`doc` in :class:`DocumentSet`.

        :param doc: The doc needs to be appended.
        :return: Appended list.
        """
        return self._docs_proto.append(doc.proto)

    def add(self, doc: 'Document') -> 'Document':
        """Shortcut to :meth:`append`, do not override this method.

        :param doc: the document to add to the set
        :return: Appended list.
        """
        return self.append(doc)

    def extend(self, iterable: Iterable['Document']) -> None:
        """
        Extend the :class:`DocumentSet` by appending all the items from the iterable.

        :param iterable: the iterable of Documents to extend this set with
        """
        for doc in iterable:
            self.append(doc)

    def clear(self):
        """Clear the data of :class:`DocumentSet`"""
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

    def build(self):
        """Build a doc_id to doc mapping so one can later index a Document using doc_id as string key."""
        self._docs_map = {d.id: d for d in self._docs_proto}

    def sort(self, *args, **kwargs):
        """
        Sort the items of the :class:`DocumentSet` in place.

        :param args: variable set of arguments to pass to the sorting underlying function
        :param kwargs: keyword arguments to pass to the sorting underlying function
        """
        self._docs_proto.sort(*args, **kwargs)

    @property
    def all_embeddings(self) -> Tuple['np.ndarray', 'DocumentSet']:
        """Return all embeddings from every document in this set as a ndarray

        :return: The corresponding documents in a :class:`DocumentSet`,
                and the documents have no embedding in a :class:`DocumentSet`.
        :rtype: A tuple of embedding in :class:`np.ndarray`
        """
        return self.extract_docs('embedding', stack_contents=True)

    def get_all_sparse_embeddings(
        self, embedding_cls_type: EmbeddingClsType
    ) -> Tuple['SparseEmbeddingType', 'DocumentSet']:
        """Return all embeddings from every document in this set as a sparse array

        :param embedding_cls_type: Type of sparse matrix backend, e.g. `scipy`, `torch` or `tf`.

        :return: The corresponding documents in a :class:`DocumentSet`,
            and the documents have no embedding in a :class:`DocumentSet`.
        :rtype: A tuple of embedding and DocumentSet as sparse arrays
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

    @property
    def all_contents(self) -> Tuple['np.ndarray', 'DocumentSet']:
        """Return all embeddings from every document in this set as a ndarray

        :return: The corresponding documents in a :class:`DocumentSet`,
                and the documents have no contents in a :class:`DocumentSet`.
        :rtype: A tuple of embedding in :class:`np.ndarray`
        """
        # stack true for backward compatibility, but will not work if content is blob of different shapes
        return self.extract_docs('content', stack_contents=True)

    def extract_docs(
        self, *fields: str, stack_contents: Union[bool, List[bool]] = False
    ) -> Tuple[Union['np.ndarray', List['np.ndarray']], 'DocumentSet']:
        """Return in batches all the values of the fields

        :param fields: Variable length argument with the name of the fields to extract
        :param stack_contents: boolean flag indicating if output lists should be stacked with `np.stack`
        :return: Returns an :class:`np.ndarray` or a list of :class:`np.ndarray` with the batches for these fields
        """

        list_of_contents_output = len(fields) > 1
        contents = [[] for _ in fields if list_of_contents_output]
        docs_pts = []
        bad_docs = []

        if list_of_contents_output:
            for doc in self:
                content = doc.get_attrs_values(*fields)
                if content is None:
                    bad_docs.append(doc)
                    continue
                for i, c in enumerate(content):
                    contents[i].append(c)
                docs_pts.append(doc)
            for idx, c in enumerate(contents):
                if not c:
                    continue
                if (
                    isinstance(stack_contents, bool)
                    and stack_contents
                    and not isinstance(c[0], bytes)
                ) or (
                    isinstance(stack_contents, list)
                    and stack_contents[idx]
                    and not isinstance(c[0], bytes)
                ):
                    contents[idx] = np.stack(c)
        else:
            for doc in self:
                content = doc.get_attrs_values(*fields)[0]
                if content is None:
                    bad_docs.append(doc)
                    continue
                contents.append(content)
                docs_pts.append(doc)

            if not contents:
                contents = None
            elif (
                isinstance(stack_contents, bool)
                and stack_contents
                and not isinstance(contents[0], bytes)
            ) or (
                isinstance(stack_contents, list)
                and stack_contents[0]
                and not isinstance(contents[0], bytes)
            ):
                contents = np.stack(contents)

        if bad_docs:
            default_logger.warning(
                f'found {len(bad_docs)} docs at granularity {bad_docs[0].granularity} are missing one of the '
                f'following fields: {fields} '
            )

        if not docs_pts:
            default_logger.warning('no documents are extracted')

        return contents, DocumentSet(docs_pts)

    def __bool__(self):
        """To simulate ```l = []; if l: ...```

        :return: returns true if the length of the set is larger than 0
        """
        return len(self) > 0

    def new(self) -> 'Document':
        """Create a new empty document appended to the end of the set.

        :return: a new Document appended to the set
        """
        from ..document import Document

        return self.append(Document())

    def __str__(self):
        from ..document import Document

        content = ',\n'.join(str(Document(d)) for d in self._docs_proto[:3])
        if len(self._docs_proto) > 3:
            content += f'in total {len(self._docs_proto)} items'
        return content

    def __repr__(self):
        content = ' '.join(
            f'{k}={v}' for k, v in {'length': len(self._docs_proto)}.items()
        )
        content += f' at {id(self)}'
        content = content.strip()
        return f'<{typename(self)} {content}>'
