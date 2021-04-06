from jina.executors.compound import CompoundExecutor
from jina.executors.indexers.query import BaseQueryIndexer


class QueryCompoundExecutor(CompoundExecutor, BaseQueryIndexer):
    """A Compound Executor that wraps several QueryIndexers"""

    # def get_query_handler(self):
    #     """Get a *readable* index handler when the ``index_abspath`` already exist, need to be overridden"""
    #     return 0
    #
    # def get_add_handler(self):
    #     """Get a *writable* index handler when the ``index_abspath`` already exist, need to be overridden"""
    #     return 0
    #
    # def get_create_handler(self):
    #     """Get a *writable* index handler when the ``index_abspath`` does not exist, need to be overridden"""
    #     return 0

    def load_dump(self, path, *args, **kwargs):
        """Loads the data in the indexer

        :param path: the path to the dump
        :param args: passed to the inner Indexer's load_dump
        :param kwargs: passed to the inner Indexer's load_dump
        """
        for c in self.components:
            c.load_dump(path)
