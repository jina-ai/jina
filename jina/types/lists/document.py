from collections.abc import MutableSequence
from typing import Union, Iterable, Tuple, Sequence, List

import numpy as np

from ...helper import typename
from ...logging import default_logger

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

if False:
    from ..document import Document

__all__ = ['DocumentList']


class DocumentList(TraversableSequence, MutableSequence):
    """
    :class:`DocumentList` is a mutable sequence of :class:`Document`.
    It gives an efficient view of a list of Document. One can iterate over it like
    a generator but ALSO modify it, count it, get item, or union two 'DocumentList's using the '+' and '+=' operators.

    :param docs_proto: A list of :class:`Document`
    :type docs_proto: Union['RepeatedContainer', Sequence['Document']]
    """

    def __init__(self, docs_proto: Union['RepeatedContainer', Sequence['Document']]):
        super().__init__()
        self._docs_proto = docs_proto
        self._docs_map = {}

    def insert(self, index: int, doc: 'Document') -> None:
        """
        Insert :param:`doc.proto` at :param:`index` into the list of `:class:`DocumentList` .

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

    def __iter__(self):
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
            return DocumentList(self._docs_proto[item])
        else:
            raise IndexError(f'do not support this index {item}')

    def __add__(self, other: 'DocumentList'):
        v = DocumentList([])
        for doc in self:
            v.add(doc)
        for doc in other:
            v.add(doc)
        return v

    def __iadd__(self, other: 'DocumentList'):
        for doc in other:
            self.add(doc)
        return self

    def append(self, doc: 'Document') -> 'Document':
        """
        Append :param:`doc` in :class:`DocumentList`.

        :param doc: The doc needs to be appended.
        :return: Appended list.
        """
        return self._docs_proto.append(doc.proto)

    def add(self, doc: 'Document') -> 'Document':
        """Shortcut to :meth:`append`, do not override this method.

        :param doc: the document to add to the list
        :return: Appended list.
        """
        return self.append(doc)

    def extend(self, iterable: Iterable['Document']) -> None:
        """
        Extend the :class:`DocumentList` by appending all the items from the iterable.

        :param iterable: the iterable of Documents to extend this list with
        """
        for doc in iterable:
            self.append(doc)

    def clear(self):
        """Clear the data of :class:`DocumentList`"""
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
        Sort the items of the :class:`DocumentList` in place.

        :param args: variable list of arguments to pass to the sorting underlying function
        :param kwargs: keyword arguments to pass to the sorting underlying function
        """
        self._docs_proto.sort(*args, **kwargs)

    @property
    def all_embeddings(self) -> Tuple['np.ndarray', 'DocumentList']:
        """Return all embeddings from every document in this list as a ndarray

        :return: The corresponding documents in a :class:`DocumentList`,
                and the documents have no embedding in a :class:`DocumentList`.
        :rtype: A tuple of embedding in :class:`np.ndarray`
        """
        return self.extract_docs('embedding', stack_contents=True)

    @property
    def all_contents(self) -> Tuple['np.ndarray', 'DocumentList']:
        """Return all embeddings from every document in this list as a ndarray

        :return: The corresponding documents in a :class:`DocumentList`,
                and the documents have no contents in a :class:`DocumentList`.
        :rtype: A tuple of embedding in :class:`np.ndarray`
        """
        # stack true for backward compatibility, but will not work if content is blob of different shapes
        return self.extract_docs('content', stack_contents=True)

    def extract_docs(
        self, *fields: str, stack_contents: bool = False
    ) -> Tuple[Union['np.ndarray', List['np.ndarray']], 'DocumentList']:
        """Return in batches all the values of the fields

        :param fields: Variable length argument with the name of the fields to extract
        :param stack_contents: boolean flag indicating if output lists should be stacked with `np.stack`
        :return: Returns an :class:`np.ndarray` or a list of :class:`np.ndarray` with the batches for these fields
        """

        list_of_contents_output = len(fields) > 1
        contents = [[] for _ in fields if len(fields) > 1]
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
                if stack_contents and not isinstance(c[0], bytes):
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
            elif stack_contents and not isinstance(contents[0], bytes):
                contents = np.stack(contents)

        if bad_docs:
            default_logger.warning(
                f'found {len(bad_docs)} docs at granularity {bad_docs[0].granularity} are missing one of the '
                f'following fields: {fields} '
            )

        return contents, DocumentList(docs_pts)

    def __bool__(self):
        """To simulate ```l = []; if l: ...```

        :return: returns true if the length of the list is larger than 0
        """
        return len(self) > 0

    def new(self) -> 'Document':
        """Create a new empty document appended to the end of the list.

        :return: a new Document appended to the list
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
