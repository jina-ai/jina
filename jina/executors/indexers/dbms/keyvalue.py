import pickle

from jina.executors.dump import DumpPersistor
from jina.executors.indexers.dbms import BaseDBMSIndexer
from jina.executors.indexers.keyvalue import BinaryPbIndexer


class DBMSBinaryPbIndexer(BinaryPbIndexer, BaseDBMSIndexer):
    def _get_generator(self, ids):
        for id_ in ids:
            vecs_metas_bytes = super().query(id_)
            vec, meta = pickle.loads(vecs_metas_bytes)
            yield id_, vec, meta

    def dump(self, path, shards, formats) -> None:
        self.write_handler.close()
        del self.write_handler
        self.handler_mutex = False
        ids = self.query_handler.header.keys()
        # TODO split for shards
        DumpPersistor.export_dump_streaming(path, self._get_generator(ids))
        self.query_handler.close()
        self.handler_mutex = False
        del self.query_handler

    def add(self, ids, vecs, metas, *args, **kwargs):
        vecs_metas = [pickle.dumps((vec, meta)) for vec, meta in zip(vecs, metas)]
        super().add(ids, vecs_metas)

    def update(self, ids, vecs, metas, *args, **kwargs):
        raise NotImplementedError

    def delete(self, ids, *args, **kwargs):
        raise NotImplementedError
