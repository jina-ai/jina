from jina.executors.compound import CompoundExecutor
from jina.executors.indexers.query import QueryReloadIndexer


class QueryCompoundExecutor(CompoundExecutor, QueryReloadIndexer):
    def get_query_handler(self):
        """Get a *readable* index handler when the ``index_abspath`` already exist, need to be overridden"""
        return 0

    def get_add_handler(self):
        """Get a *writable* index handler when the ``index_abspath`` already exist, need to be overridden"""
        return 0

    def get_create_handler(self):
        """Get a *writable* index handler when the ``index_abspath`` does not exist, need to be overridden"""
        return 0

    def reload(self, path, *args, **kwargs):
        print(f'### calling reload of QueryCompound')
        for c in self.components:
            print(f'compound passing import req to {c}')
            c.reload(path)
