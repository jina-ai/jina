from typing import Optional

from jina.executors.indexers.dump import import_metas
from jina.executors.indexers.keyvalue import BinaryPbWriterMixin
from jina.executors.indexers.query import BaseQueryIndexer


class BinaryPbQueryIndexer(BinaryPbWriterMixin, BaseQueryIndexer):
    """A write-once Key-value indexer."""

    def _load_dump(self, dump_path):
        """Load the dump at the path

        :param dump_path: the path of the dump"""
        ids, metas = import_metas(dump_path, str(self.pea_id))
        self._add(list(ids), list(metas))
        self.write_handler.flush()
        self.write_handler.close()
        self.handler_mutex = False
        self.is_handler_loaded = False
        del self.write_handler
        # warming up
        self._query('someid')

    def query(self, key: str, *args, **kwargs) -> Optional[bytes]:
        """Get a document by its id

        :param key: the id
        :param args: not used
        :param kwargs: not used
        :return: the bytes of the Document
        """
        return self._query(key)


class KeyValueQueryIndexer(BinaryPbQueryIndexer):
    """An alias"""
