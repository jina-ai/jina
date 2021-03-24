from jina.executors.indexers import BaseIndexer


class QueryReloadIndexer(BaseIndexer):
    def import_uri_path(self, path):
        raise NotImplementedError
