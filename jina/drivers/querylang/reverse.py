__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable, Tuple

from .. import QuerySetReader, BaseRecursiveDriver

if False:
    from ...proto import jina_pb2


class ReverseQL(QuerySetReader, BaseRecursiveDriver):
    """Reverses the order of the provided ``docs``.

        This is often useful when the proceeding Pods require only a signal, not the full message.

        Example ::
        - !Chunk2DocRankerDriver {}
        - !ReverseQL {}

        will reverse the order of the documents returned by the `Chunk2DocRankerDriver` before sending them to the next `Pod`
    """

    def __init__(self, traversal_paths: Tuple[str] = ('c',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs) -> None:
        prev_len = len(docs)
        for d in reversed(docs):
            dd = docs.add()
            dd.CopyFrom(d)
        del docs[:prev_len]
