from typing import Iterator
from . import BaseIndexer


class DuplicateChecker(BaseIndexer):

    class EmptyHandler:
        def __init__(self):
            pass

        def close(self):
            pass

        def flush(self):
            pass

        def write(self, *args, **kwargs):
            pass

    def __init__(self, *args, **kwargs):
        super().__init__(index_filename='', *args, **kwargs)
        self.indexed = set()
        self._size = self._indexed_size

    def _filter_ids(self, id_list):
        is_indexed = []
        for id in id_list:
            _indexed = (id in self.indexed)
            is_indexed.append(_indexed)
            if not _indexed:
                self.indexed.add(id)
        return is_indexed

    def add(self, ids: Iterator[int], *args, **kwargs):
        is_indexed = self._filter_ids(ids)
        return is_indexed

    def query(self, ids: Iterator[int], *args, **kwargs):
        return self._filter_ids(ids)

    def get_add_handler(self):
        return self.EmptyHandler()

    def get_create_handler(self):
        return self.EmptyHandler()

    def get_query_handler(self):
        return self.EmptyHandler()

    @property
    def _indexed_size(self):
        return len(self.indexed)