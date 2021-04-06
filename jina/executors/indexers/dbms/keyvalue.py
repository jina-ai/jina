import pickle
from typing import List, Optional

from jina.executors.dump import DumpTypes, DumpPersistor
from jina.executors.indexers.dbms import BaseDBMSIndexer
from jina.executors.indexers.keyvalue import BinaryPbIndexer


class DBMSBinaryPbIndexer(BinaryPbIndexer, BaseDBMSIndexer):
    """A DBMS Indexer (no query method)"""

    def _get_generator(self, ids):
        for id_ in ids:
            vecs_metas_bytes = super().query(id_)
            vec, meta = pickle.loads(vecs_metas_bytes)
            yield id_, vec, meta

    def dump(self, path: str, shards: int, formats: List[DumpTypes]) -> None:
        """Dump the index with the DumpPersistor

        :param path: the path to which to dump
        :param shards: the nr of shards to which to dump
        :param formats: the list of formats
        """
        self.write_handler.close()
        # noinspection PyPropertyAccess
        del self.write_handler
        self.handler_mutex = False
        ids = self.query_handler.header.keys()
        DumpPersistor.export_dump_streaming(
            path,
            shards=shards,
            size=self.size,
            data=self._get_generator(ids),
            formats=formats,
        )
        self.query_handler.close()
        self.handler_mutex = False
        # noinspection PyPropertyAccess
        del self.query_handler

    # noinspection PyMethodOverriding
    # we subclass from BinaryPb to get the add/delete/update methods.
    # this class just wraps around those
    def add(self, ids, vecs, metas, *args, **kwargs):
        """Add to the DBMS Indexer, both vectors and metadata

        :param ids: the ids of the documents
        :param vecs: the vectors
        :param metas: the metadata, in binary format
        :param args: not used
        :param kwargs: not used
        """
        vecs_metas = [pickle.dumps((vec, meta)) for vec, meta in zip(vecs, metas)]
        BinaryPbIndexer.add(self, ids, vecs_metas)

    # noinspection PyMethodOverriding
    def update(self, ids, vecs, metas, *args, **kwargs):
        """Update the DBMS Indexer, both vectors and metadata

        :param ids: the ids of the documents
        :param vecs: the vectors
        :param metas: the metadata, in binary format
        :param args: not used
        :param kwargs: not used
        """
        values = [pickle.dumps((vec, meta)) for vec, meta in zip(vecs, metas)]
        keys, values = self._filter_nonexistent_keys_values(
            ids, values, self.query_handler.header.keys()
        )
        del self.query_handler
        self.handler_mutex = False
        if keys:
            self._delete(keys)
            # TODO refactor requires _filter_nonexistent_keys_values to accept *args for lists
            BinaryPbIndexer.add(self, keys, values)

    def delete(self, ids, *args, **kwargs):
        """Delete from the indexer by ids

        :param ids: the ids of the Documents to delete
        :param args: not used
        :param kwargs: not used
        """
        super().delete(ids)

    def query(self, key: str, *args, **kwargs) -> Optional[bytes]:
        """DBMSIndexers do NOT support querying

        :param key: the key by which to query
        :param args: not used
        :param kwargs: not used
        """
        raise NotImplementedError('DBMSIndexers do not support querying')


class DBMSKeyValueIndexer(DBMSBinaryPbIndexer):
    """An alias"""
