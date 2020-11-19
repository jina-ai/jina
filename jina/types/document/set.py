from collections import MutableSequence
from typing import Iterable

from google.protobuf.pyext._message import RepeatedCompositeContainer

from . import Document


class DocumentSet(MutableSequence):
    """:class:`DocumentSet` is a mutable sequence of :class:`Document`,
    it gives an efficient view of a list of Document. One can iterate over it like
    a generator but also modify it.


    """
    def __init__(self, docs_proto: 'RepeatedCompositeContainer'):
        super().__init__()
        self._docs_proto = docs_proto

    def insert(self, index: int, doc: 'Document') -> None:
        self._docs_proto.insert(index, doc.as_pb_object)

    def __setitem__(self, key, value: 'Document'):
        self._docs_proto[key].CopyFrom(value.as_pb_object)

    def __delitem__(self, index):
        del self._docs_proto[index]

    def __len__(self):
        return len(self._docs_proto)

    def __iter__(self):
        for d in self._docs_proto:
            yield Document(d)

    def __getitem__(self, item):
        return Document(self._docs_proto[item])

    def append(self, doc: 'Document'):
        self._docs_proto.append(doc.as_pb_object)

    def extend(self, iterable: Iterable['Document']) -> None:
        self._docs_proto.extend(doc.as_pb_object for doc in iterable)

    def clear(self):
        del self._docs_proto[:]

    def reverse(self):
        size = len(self._docs_proto)  # Get the length of the sequence
        hi_idx = size - 1
        its = size / 2  # Number of iterations required

