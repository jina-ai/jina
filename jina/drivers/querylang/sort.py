__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable, Tuple

from ...types.querylang.queryset.dunderkey import dunder_get
from .. import QuerySetReader, ContextAwareRecursiveMixin, BaseRecursiveDriver

if False:
    from ...types.sets import DocumentSet


class SortQL(QuerySetReader, ContextAwareRecursiveMixin, BaseRecursiveDriver):
    """Sorts the incoming of the documents by the value of a given field.
    It can also work in reverse mode

       Example::
       - !ReduceAllDriver
           with:
               traversal_paths: ['m']
       - !SortQL
           with:
               reverse: true
               field: 'score__value'
               traversal_paths: ['m']
       - !SliceQL
           with:
               start: 0
               end: 50
               traversal_paths: ['m']

       `SortQL` will ensure that only the documents are sorted by the score value before slicing the first top 50 documents
        :param field: the value of the field drives the sort of the iterable docs
        :param reverse: sort the value from big to small
        :param traversal_paths: the traversal paths
        :param args: additional positional arguments which are just used for the parent initialization
        :param kwargs: additional key value arguments which are just used for the parent initialization
    """

    def __init__(
        self,
        field: str,
        reverse: bool = False,
        traversal_paths: Tuple[str] = ('r',),
        *args,
        **kwargs
    ):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)
        self._reverse = reverse
        self._field = field

    def _apply_all(
        self, doc_sequences: Iterable['DocumentSet'], *args, **kwargs
    ) -> None:
        for docs in doc_sequences:
            docs.sort(key=lambda x: dunder_get(x, self.field), reverse=self.reverse)
