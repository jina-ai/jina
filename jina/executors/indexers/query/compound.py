from jina.executors.compound import CompoundExecutor
from jina.executors.indexers.query import BaseQueryIndexer


class QueryCompoundExecutor(CompoundExecutor, BaseQueryIndexer):
    """A Compound Executor that wraps several QueryIndexers"""

    def load_dump(self, path, *args, **kwargs):
        """Loads the data in the indexer

        :param path: the path to the dump
        :param args: passed to the inner Indexer's load_dump
        :param kwargs: passed to the inner Indexer's load_dump
        """
        for c in self.components:
            c.load_dump(path)
