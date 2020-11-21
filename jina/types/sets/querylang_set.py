from collections.abc import MutableSequence
from typing import Iterable

from google.protobuf.pyext._message import RepeatedCompositeContainer

from ..querylang import QueryLang
from ...proto.jina_pb2 import QueryLangProto

__all__ = ['QueryLangSet']


class QueryLangSet(MutableSequence):
    """:class:`QueryLangSet` is a mutable sequence of :class:`QueryLang`,
    it gives an efficient view of a list of Document. One can iterate over it like
    a generator but ALSO modify it, count it, get item.
    """

    def __init__(self, querylang_protos: 'RepeatedCompositeContainer'):
        super().__init__()
        self._querylangs_proto = querylang_protos
        self._querylangs_map = {}

    def insert(self, index: int, ql: 'QueryLang') -> None:
        self._querylangs_proto.insert(index, ql.as_pb_object)

    def __setitem__(self, key, value: 'QueryLang'):
        if isinstance(key, int):
            self._querylangs_proto[key].CopyFrom(value.as_pb_object)
        elif isinstance(key, str):
            return self._querylangs_map[key].CopyFrom(value.as_pb_object)
        else:
            raise IndexError(f'do not support this index {key}')

    def __delitem__(self, index):
        del self._querylangs_proto[index]

    def __len__(self):
        return len(self._querylangs_proto)

    def __iter__(self):
        for d in self._querylangs_proto:
            yield QueryLang(d)

    def __getitem__(self, item):
        if isinstance(item, int):
            return QueryLang(self._querylangs_proto[item])
        elif isinstance(item, str):
            return QueryLang(self._querylangs_map[item])
        else:
            raise IndexError(f'do not support this index {item}')

    def append(self, doc: 'QueryLang'):
        self._querylangs_proto.append(doc.as_pb_object)

    def extend(self, iterable: Iterable['QueryLang']) -> None:
        self._querylangs_proto.extend(doc.as_pb_object for doc in iterable)

    def clear(self):
        del self._querylangs_proto[:]

    def reverse(self):
        size = len(self._querylangs_proto)
        hi_idx = size - 1
        for i in range(int(size / 2)):
            tmp = QueryLangProto()
            tmp.CopyFrom(self._querylangs_proto[hi_idx])
            self._querylangs_proto[hi_idx].CopyFrom(self._querylangs_proto[i])
            self._querylangs_proto[i].CopyFrom(tmp)
            hi_idx -= 1

    def build(self):
        """Build a doc_id to doc mapping so one can later index a Document using
        doc_id as string key
        """
        self._docs_map = {d.id: d for d in self._querylangs_proto}
