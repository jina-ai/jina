from typing import Optional, List

from jina import Document
from jina.executors.indexers.dump import import_metas
from jina.executors.indexers.keyvalue import BinaryPbWriterMixin
from jina.executors.indexers.query import BaseQueryIndexer


class BinaryPbQueryIndexer(BinaryPbWriterMixin, BaseQueryIndexer):
    """A write-once Key-value indexer."""

    def _load_dump(self, dump_path):
        """Load the dump at the path

        :param dump_path: the path of the dump"""
        ids, metas = import_metas(dump_path, str(self.pea_id))
        # ids = list(ids)
        # metas = list(metas)
        # for id, meta in zip(ids, metas):
        #     print(f'### adding to query: {id=}; {meta}')
        #     d = Document(meta)
        #     assert d.tags['tag_field'] == f'tag data {d.id}'
        with self.get_create_handler() as write_handler:
            self._add(list(ids), list(metas), write_handler)
        # warming up
        self.query(['someid'])

    def query(self, keys: List[str], *args, **kwargs) -> List[Optional[bytes]]:
        """Get a document by its id

        :param keys: the ids
        :param args: not used
        :param kwargs: not used
        :return: List of the bytes of the Documents (or None, if not found)
        """
        res = self._query(keys)
        # print(f'### comparison::')
        # for k, r in zip(keys, res):
        #     try:
        #         print(f'### {k=}; {r=}')
        #         assert Document(r), f'{keys=}'
        #     except Exception as e:
        #         print(e)
        return res


class KeyValueQueryIndexer(BinaryPbQueryIndexer):
    """An alias"""
