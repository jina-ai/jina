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
        super().__init__(*args, **kwargs)
        self.ids = set()

    def _filter_ids(self, ids):
        _filtered = []
        for id in ids:
            if id in self.ids:
                continue
            self.ids.add(id)
            _filtered.append(id)
        return _filtered

    def add(self, ids: Iterator[int], *args, **kwargs):
        filtered_ids = self._filter_ids(ids)
        self._size += len(filtered_ids)
        return filtered_ids

    def query(self, ids: Iterator[int], *args, **kwargs):
        return self._filter_ids(ids)

    def get_add_handler(self):
        return self.EmptyHandler()

    def get_create_handler(self):
        return self.EmptyHandler()

    def get_query_handler(self):
        return self.EmptyHandler()
