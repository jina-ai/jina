from typing import List

from jina.executors.reload_helpers import DumpTypes


class DumpableIndexer:
    def add(self, ids, vectors, metadata):
        raise NotImplementedError

    def dump(self, path: str, shards: int, formats: List[DumpTypes]) -> None:
        raise NotImplementedError
