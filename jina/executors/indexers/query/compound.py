from jina.executors.compound import CompoundExecutor
from jina.executors.indexers.query import QueryReloadIndexer


class QueryCompoundExecutor(CompoundExecutor, QueryReloadIndexer):
    """TODO"""

    def get_query_handler(self):
        """Get a *readable* index handler when the ``index_abspath`` already exist, need to be overridden"""
        return 0

    def get_add_handler(self):
        """Get a *writable* index handler when the ``index_abspath`` already exist, need to be overridden"""
        return 0

    def get_create_handler(self):
        """Get a *writable* index handler when the ``index_abspath`` does not exist, need to be overridden"""
        return 0

    def import_uri_path(self, path):
        """TODO

        :param path:
        """
        for c in self.components:
            c.import_uri_path(path)
