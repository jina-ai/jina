from collections.abc import MutableSequence
from typing import Iterable, Union, Dict


try:
    # when protobuf using Cpp backend
    from google.protobuf.pyext._message import RepeatedCompositeContainer as RepeatedContainer
except:
    # when protobuf using Python backend
    from google.protobuf.internal.containers import RepeatedCompositeFieldContainer as RepeatedContainer


from ..querylang import QueryLang
from ...helper import typename
from ...proto.jina_pb2 import QueryLangProto

AcceptQueryLangType = Union[QueryLang, QueryLangProto, Dict]

__all__ = ['QueryLangSet', 'AcceptQueryLangType']


class QueryLangSet(MutableSequence):
    """:class:`QueryLangSet` is a mutable sequence of :class:`QueryLang`,
    it gives an efficient view of a list of Document. One can iterate over it like
    a generator but ALSO modify it, count it, get item.
    """

    def __init__(self, querylang_protos: 'RepeatedContainer'):
        super().__init__()
        self._querylangs_proto = querylang_protos
        self._querylangs_map = {}

    def insert(self, index: int, ql: 'QueryLang') -> None:
        self._querylangs_proto.insert(index, ql.proto)

    def __setitem__(self, key, value: 'QueryLang'):
        if isinstance(key, int):
            self._querylangs_proto[key].CopyFrom(value.proto)
        elif isinstance(key, str):
            self._querylangs_map[key].CopyFrom(value.proto)
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

    def append(self, value: 'AcceptQueryLangType'):
        q_pb = self._querylangs_proto.add()
        if isinstance(value, Dict):
            q_pb.CopyFrom(QueryLang(value).proto)
        elif isinstance(value, QueryLangProto):
            q_pb.CopyFrom(value)
        elif isinstance(value, QueryLang):
            q_pb.CopyFrom(value.proto)
        else:
            raise TypeError(f'unknown type {typename(value)}')

    def extend(self, iterable: Iterable[AcceptQueryLangType]) -> None:
        for q in iterable:
            self.append(q)

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
        """Build a name to QueryLang mapping so one can later index a QueryLang using
        name as string key
        """
        # TODO This is a temp fix, QueryLangProto do not have an id field.
        self._querylangs_map = {q.name: q for q in self._querylangs_proto}
