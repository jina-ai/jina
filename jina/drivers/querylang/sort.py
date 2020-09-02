__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

from .. import QuerySetReader, BaseRecursiveDriver
from ...helper import rgetattr

if False:
    from ...proto import jina_pb2


class SortQL(QuerySetReader, BaseRecursiveDriver):
    """Sorts the incoming of the documents by the value of a given field.
     It can also work in reverse mode

        Example::
        - !ReduceAllDriver
            with:
                recur_on: matches
        - !SortQL
            with:
                reverse: true
                field: 'score.value'
                recur_on: matches
        - !SliceQL
            with:
                start: 0
                end: 50
                recur_on: matches

        `SortQL` will ensure that only the documents are sorted by the score value before slicing the first top 50 documents
    """

    def __init__(self, field: str, reverse: bool = False, *args, **kwargs):
        """
        :param field: the value of the field drives the sort of the iterable docs
        :param reverse: sort the value from big to small
        """

        super().__init__(*args, **kwargs)
        self._reverse = reverse
        self._field = field
        self.is_apply = False

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        docs.sort(key=lambda x: rgetattr(x, self.field), reverse=self.reverse)

