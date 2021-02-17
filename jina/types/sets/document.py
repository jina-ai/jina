from collections.abc import MutableSequence
from typing import Union, Iterable, Tuple

import numpy as np

from ...helper import typename
from ...logging import default_logger

try:
    # when protobuf using Cpp backend
    from google.protobuf.pyext._message import RepeatedCompositeContainer as RepeatedContainer
except:
    # when protobuf using Python backend
    from google.protobuf.internal.containers import RepeatedCompositeFieldContainer as RepeatedContainer

from ...proto.jina_pb2 import DocumentProto

if False:
    from ..document import Document

__all__ = ['DocumentSet']


class DocumentSet(MutableSequence):
    """
    :class:`DocumentSet` is a mutable sequence of :class:`Document`.
    It gives an efficient view of a list of Document. One can iterate over it like
    a generator but ALSO modify it, count it, get item, or union two 'DocumentSet's using the '+' and '+=' operators.

    :param docs_proto: A list of :class:`Document`
    :type docs_proto: Union['RepeatedContainer', Sequence['Document']]
    """

    def __init__(self, docs_proto: Union['RepeatedContainer', Iterable['Document']]):
        """Set constructor method."""
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
        """Shortcut to :meth:`append`, do not override this method."""
        return self.append(doc)

    def extend(self, iterable: Iterable['Document']) -> None:
        """Extend an iterable to :class:`DocumentSet`."""
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
        """Sort the list of :class:`DocumentSet`."""
        self._docs_proto.sort(*args, **kwargs)

    def traverse(self, traversal_paths: Iterable[str]) -> 'DocumentSet':
        """
        Return a DocumentSet that traverses this :class:`DocumentSet` object according to the
        ``traversal_paths``.

        :param traversal_paths: a list of string that represents the traversal path


        Example on ``traversal_paths``:

            - [`r`]: docs in this DocumentSet
            - [`m`]: all match-documents at adjacency 1
            - [`c`]: all child-documents at granularity 1
            - [`cc`]: all child-documents at granularity 2
            - [`mm`]: all match-documents at adjacency 2
            - [`cm`]: all match-document at adjacency 1 and granularity 1
            - [`r`, `c`]: docs in this DocumentSet and all child-documents at granularity 1

        """

        def _traverse(docs: 'DocumentSet', path: str):
            if path:
                loc = path[0]
                if loc == 'r':
                    yield from _traverse(docs, path[1:])
                elif loc == 'm':
                    for d in docs:
                        yield from _traverse(d.matches, path[1:])
                elif loc == 'c':
                    for d in docs:
                        yield from _traverse(d.chunks, path[1:])
            else:
                yield from docs

        def _traverse_all():
            for p in traversal_paths:
                yield from _traverse(self, p)

        return DocumentSet(_traverse_all())

    @property
    def all_embeddings(self) -> Tuple['np.ndarray', 'DocumentSet']:
        """Return all embeddings from every document in this set as a ndarray

        :return: The corresponding documents in a :class:`DocumentSet`,
                and the documents have no embedding in a :class:`DocumentSet`.
        :rtype: A tuple of embedding in :class:`np.ndarray`
        """
        return self._extract_docs('embedding')

    @property
    def all_contents(self) -> Tuple['np.ndarray', 'DocumentSet']:
        """Return all embeddings from every document in this set as a ndarray

        :return: The corresponding documents in a :class:`DocumentSet`,
                and the documents have no contents in a :class:`DocumentSet`.
        :rtype: A tuple of embedding in :class:`np.ndarray`
        """
        return self._extract_docs('content')

    def _extract_docs(self, attr: str) -> Tuple['np.ndarray', 'DocumentSet']:
        contents = []
        docs_pts = []
        bad_docs = []

        for doc in self:
            content = getattr(doc, attr)

            if content is not None:
                contents.append(content)
                docs_pts.append(doc)
            else:
                bad_docs.append(doc)

        contents = np.stack(contents) if contents else None

        if bad_docs and docs_pts:
            default_logger.warning(
                f'found {len(bad_docs)} no-{attr} docs at granularity {docs_pts[0].granularity}')

        return contents, DocumentSet(docs_pts)

    def __bool__(self):
        """To simulate ```l = []; if l: ...``` """
        return len(self) > 0

    def new(self) -> 'Document':
        """Create a new empty document appended to the end of the set."""
        from ..document import Document
        return self.append(Document())

    def __str__(self):
        from ..document import Document
        content = ',\n'.join(str(Document(d)) for d in self._docs_proto[:3])
        if len(self._docs_proto) > 3:
            content += f'in total {len(self._docs_proto)} items'
        return content

    def __repr__(self):
        content = ' '.join(f'{k}={v}' for k, v in {'length': len(self._docs_proto)}.items())
        content += f' at {id(self)}'
        content = content.strip()
        return f'<{typename(self)} {content}>'
