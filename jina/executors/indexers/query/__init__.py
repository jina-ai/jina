from jina.executors.indexers import BaseIndexer


class QueryReloadIndexer(BaseIndexer):
    def reload(self, path):
        raise NotImplementedError
