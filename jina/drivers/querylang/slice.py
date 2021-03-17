__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import sys

from typing import Iterable, Optional

from .. import QuerySetReader, ContextAwareRecursiveMixin, BaseRecursiveDriver

if False:
    from ...types.sets.document import DocumentSet


class SliceQL(QuerySetReader, ContextAwareRecursiveMixin, BaseRecursiveDriver):
    """Restrict the size of the ``docs`` to ``k`` (given by the request)

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

    `SliceQL` will ensure that only the first 50 documents are returned from this `Pod`

    :param start: Zero-based index at which to start extraction.
    :param end:  Zero-based index before which to end extraction.
            slice extracts up to but not including end. For example, take(1,4) extracts
            the second element through the fourth element (elements indexed 1, 2, and 3).
    :param args: additional positional arguments which are just used for the parent initialization
    :param kwargs: additional key value arguments which are just used for the parent initialization
    """

    def __init__(self, start: int, end: Optional[int] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._start = int(start)
        if end is None:
            self._end = sys.maxsize
        else:
            self._end = int(end)

    def _apply_all(
        self, doc_sequences: Iterable['DocumentSet'], *args, **kwargs
    ) -> None:
        for docs in doc_sequences:
            if self.start <= 0 and (self.end is None or self.end >= len(docs)):
                pass
            else:
                del docs[int(self.end) :]
                del docs[: int(self.start)]
