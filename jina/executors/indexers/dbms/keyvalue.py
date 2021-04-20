import pickle
from typing import List, Tuple, Generator
import numpy as np

from jina.executors.indexers.dump import export_dump_streaming
from jina.executors.indexers.dbms import BaseDBMSIndexer
from jina.executors.indexers.keyvalue import BinaryPbWriterMixin


class BinaryPbDBMSIndexer(BinaryPbWriterMixin, BaseDBMSIndexer):
    """A DBMS Indexer (no query method)"""

    def _get_generator(
        self, ids: List[str]
    ) -> Generator[Tuple[str, np.array, bytes], None, None]:
        for id_ in ids:
            vecs_metas_bytes = super()._query(id_)
            vec, meta = pickle.loads(vecs_metas_bytes)
            yield id_, vec, meta

    def dump(self, path: str, shards: int) -> None:
        """Dump the index

        :param path: the path to which to dump
        :param shards: the nr of shards to which to dump
        """
        self.write_handler.close()
        # noinspection PyPropertyAccess
        del self.write_handler
        self.handler_mutex = False
        ids = self.query_handler.header.keys()
        export_dump_streaming(
            path,
            shards=shards,
            size=self.size,
            data=self._get_generator(ids),
        )
        self.query_handler.close()
        self.handler_mutex = False
        # noinspection PyPropertyAccess
        del self.query_handler

    def add(
        self,
        id: List[str],
        embedding: List[np.array],
        binary_str: List[bytes],
        *args,
        **kwargs
    ):
        """Add to the DBMS Indexer, both vectors and metadata

        :param id: the ids of the documents
        :param embedding: the vectors
        :param binary_str: the metadata, in binary format
        :param args: not used
        :param kwargs: not used
        """
        if not any(id):
            return

        vecs_metas = [
            pickle.dumps((vec, meta)) for vec, meta in zip(embedding, binary_str)
        ]
        self._add(id, vecs_metas)

    def update(
        self,
        id: List[str],
        embedding: List[np.array],
        binary_str: List[bytes],
        *args,
        **kwargs
    ):
        """Update the DBMS Indexer, both vectors and metadata

        :param id: the ids of the documents
        :param embedding: the vectors
        :param binary_str: the metadata, in binary format
        :param args: not used
        :param kwargs: not used
        """
        vecs_metas = [
            pickle.dumps((vec, meta)) for vec, meta in zip(embedding, binary_str)
        ]
        keys, vecs_metas = self._filter_nonexistent_keys_values(
            id, vecs_metas, self.query_handler.header.keys()
        )
        del self.query_handler
        self.handler_mutex = False
        if keys:
            self._delete(keys)
            self._add(keys, vecs_metas)

    def delete(self, id: List[str], *args, **kwargs):
        """Delete the serialized documents from the index via document ids.

        :param id: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param args: not used
        :param kwargs: not used"""
        super(BinaryPbDBMSIndexer, self).delete(id)


class KeyValueDBMSIndexer(BinaryPbDBMSIndexer):
    """An alias"""
