import heapq
import itertools
from collections.abc import MutableSequence
from typing import (
    Union,
    Iterable,
    Iterator,
    Optional,
    Generator,
    Dict,
    Callable,
    List,
    TYPE_CHECKING,
)

from .mixins import AllMixins
from ..document import Document
from ..helper import typename
from ..proto import docarray_pb2

if TYPE_CHECKING:
    from .types import DocumentArraySourceType

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


class DocumentArray(
    AllMixins,
    MutableSequence,
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

    def __init__(self, docs: Optional['DocumentArraySourceType'] = None):
        super().__init__()
        self._pb_body = []
        if docs is not None:
            if isinstance(docs, docarray_pb2.DocumentArrayProto):
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

                from .. import DocumentArrayMemmap

                if isinstance(
                    docs, (list, tuple, Generator, DocumentArrayMemmap, itertools.chain)
                ):
                    # This would happen in the client
                    for doc in docs:
                        if isinstance(doc, Document):
                            self._pb_body.append(doc.proto)
                        elif isinstance(doc, docarray_pb2.DocumentProto):
                            self._pb_body.append(doc)
                        else:
                            raise ValueError(f'Unexpected element in an input list')
                else:
                    raise ValueError(
                        f'DocumentArray got an unexpected input {type(docs)}'
                    )
        self._id_to_index = None

    @property
    def _index_map(self) -> Dict:
        """Return the `_id_to_index` map

        :return: a Python dict.
        """
        if not self._id_to_index:
            self._update_id_to_index_map()
        return self._id_to_index

    def _update_id_to_index_map(self):
        """Update the id_to_index map by enumerating all Documents in self._pb_body.

        Very costy! Only use this function when self._pb_body is dramtically changed.
        """

        self._id_to_index = {
            d.id: i for i, d in enumerate(self._pb_body)
        }  # type: Dict[str, int]

    def insert(self, index: int, doc: 'Document') -> None:
        """Insert `doc` at `index`.

        :param index: Position of the insertion.
        :param doc: The doc needs to be inserted.
        """
        self._pb_body.insert(index, doc.proto)
        if self._id_to_index:
            self._id_to_index[doc.id] = index

    def __setitem__(self, key, value: 'Document'):
        if isinstance(key, int):
            self[key].CopyFrom(value)
            if self._id_to_index:
                self._id_to_index[value.id] = key
        elif isinstance(key, str):
            self[self._index_map[key]].CopyFrom(value)
        else:
            raise IndexError(f'do not support this index {key}')

    def __delitem__(self, index: Union[int, str, slice]):
        if isinstance(index, int):
            del self._pb_body[index]
        elif isinstance(index, str):
            del self[self._index_map[index]]
            self._index_map.pop(index)
        elif isinstance(index, slice):
            del self._pb_body[index]
        else:
            raise IndexError(
                f'do not support this index type {typename(index)}: {index}'
            )

    def __eq__(self, other):
        return (
            type(self) is type(other)
            and type(self._pb_body) is type(other._pb_body)
            and self._pb_body == other._pb_body
        )

    def __len__(self):
        return len(self._pb_body)

    def __iter__(self) -> Iterator['Document']:
        for d in self._pb_body:
            yield Document(d)

    def __contains__(self, item: str):
        return item in self._index_map

    def __getitem__(self, item: Union[int, str, slice, List]):
        if isinstance(item, int):
            return Document(self._pb_body[item])
        elif isinstance(item, str):
            return self[self._index_map[item]]
        elif isinstance(item, slice):
            return DocumentArray(self._pb_body[item])
        elif isinstance(item, list):
            return DocumentArray(self._pb_body[t] for t in item)
        else:
            raise IndexError(f'do not support this index type {typename(item)}: {item}')

    def append(self, doc: 'Document'):
        """
        Append `doc` in :class:`DocumentArray`.

        :param doc: The doc needs to be appended.
        """
        if self._id_to_index:
            self._id_to_index[doc.id] = len(self._pb_body)
        self._pb_body.append(doc.proto)

    def extend(self, docs: Iterable['Document']) -> None:
        """
        Extend the :class:`DocumentArray` by appending all the items from the iterable.

        :param docs: the iterable of Documents to extend this array with
        """
        if not docs:
            return

        for doc in docs:
            self.append(doc)

    def clear(self):
        """Clear the data of :class:`DocumentArray`"""
        del self._pb_body[:]
        if self._id_to_index:
            self._id_to_index.clear()

    def reverse(self):
        """In-place reverse the sequence."""
        size = len(self._pb_body)
        hi_idx = size - 1
        for i in range(int(size / 2)):
            tmp = docarray_pb2.DocumentProto()
            tmp.CopyFrom(self._pb_body[hi_idx])
            self._pb_body[hi_idx].CopyFrom(self._pb_body[i])
            self._pb_body[i].CopyFrom(tmp)
            hi_idx -= 1
        self._update_id_to_index_map()

    def sort(
        self,
        key: Callable,
        top_k: Optional[int] = None,
        reverse: bool = False,
    ):
        """
        Sort the items of the :class:`DocumentArray` in place.

        :param key: key callable to sort based upon
        :param top_k: make sure that the first `topk` elements are correctly sorted rather than
            sorting the entire list
        :param reverse: reverse=True will sort the list in descending order. Default is False
        """

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
        _key = key
        try:
            key(self._pb_body[0])
        except:
            _key = overriden_key

        if top_k is None or top_k >= len(self._pb_body):
            self._pb_body.sort(key=_key, reverse=reverse)
        else:
            # heap based sorting
            # makes sure that the top_k elements are correctly sorted and leaves the rest unsorted
            if _key is None:
                # heap is a list of documents
                heap = [element for element in self._pb_body]
            else:
                # heap is a list of tuples (key, document)
                heap = [
                    (_key(element), i, element)
                    for i, element in enumerate(self._pb_body)
                ]
            # if reverse use the maxheap operations for .heapify and .heappop
            heapify = heapq._heapify_max if reverse else heapq.heapify
            heappop = heapq._heappop_max if reverse else heapq.heappop

            # transform the original list to a heap and pop the top k elements
            heapify(heap)
            topk = [heappop(heap) for _ in range(top_k)]

            # get back to lists of docs from the lists of tuples
            _, _, topk = zip(*topk)
            _, _, heap = zip(*heap)
            topk, heap = list(topk), list(heap)
            # update the protobuf body
            self._pb_body = topk + heap

        self._update_id_to_index_map()

    @staticmethod
    def _flatten(sequence) -> 'DocumentArray':
        return DocumentArray(list(itertools.chain.from_iterable(sequence)))
