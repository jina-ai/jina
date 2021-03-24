from jina.executors.indexers import BaseIndexer


class BaseDBMSIndexer(BaseIndexer):
    def add(self, ids, vecs, metas, *args, **kwargs):
        raise NotImplementedError

    def update(self, ids, vecs, metas, *args, **kwargs):
        raise NotImplementedError

    def delete(self, ids, *args, **kwargs):
        raise NotImplementedError

    def dump(self, uri, shards, formats):
        raise NotImplementedError
