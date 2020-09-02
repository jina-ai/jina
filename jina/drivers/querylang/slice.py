__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

from .. import QuerySetReader, BaseRecursiveDriver

if False:
    from ...proto import jina_pb2


class SliceQL(QuerySetReader, BaseRecursiveDriver):
    """Restrict the size of the ``docs`` to ``k`` (given by the request)

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

        `SliceQL` will ensure that only the first 50 documents are returned from this `Pod`
    """

    def __init__(self, start: int, end: int = None, *args, **kwargs):
        """

        :param start: Zero-based index at which to start extraction.
        :param end:  Zero-based index before which to end extraction.
                slice extracts up to but not including end. For example, take(1,4) extracts
                the second element through the fourth element (elements indexed 1, 2, and 3).
        """
        super().__init__(*args, **kwargs)
        self._start = int(start)
        self._end = int(end)
        self.is_apply = False

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        if self.start <= 0 and (self.end is None or self.end >= len(docs)):
            pass
        else:
            del docs[int(self.end):]
            del docs[:int(self.start)]
