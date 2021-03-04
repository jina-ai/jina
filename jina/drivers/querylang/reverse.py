__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable, Tuple

from .. import QuerySetReader, SetRecursiveMixin, BaseRecursiveDriver

if False:
    from ...types.sets import DocumentSet


class ReverseQL(QuerySetReader, SetRecursiveMixin, BaseRecursiveDriver):
    """Reverses the order of the provided ``docs``.

        This is often useful when the proceeding Pods require only a signal, not the full message.

        Example ::
        - !Chunk2DocRankerDriver {}
        - !ReverseQL {}

        will reverse the order of the documents returned by the `Chunk2DocRankerDriver` before sending them to the next `Pod`
    """

    def __init__(self, traversal_paths: Tuple[str] = ('r',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def _apply_all(self, doc_sets: Iterable['DocumentSet'], *args, **kwargs) -> None:
        for docs in doc_sets:
            docs.reverse()
