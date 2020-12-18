import tempfile
from typing import Optional, Iterator

from . import BaseKVIndexer
from ...helper import deprecated_alias, check_keys_exist
from ...types.document.uid import UniqueId

DATA_FIELD = 'data'


class BaseCache(BaseKVIndexer):
    """Base class of the cache inherited :class:`BaseKVIndexer`

    The difference between a cache and a :class:`BaseKVIndexer` is the ``handler_mutex`` is released in cache, this allows one to query-while-indexing.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_init(self):
        self.handler_mutex = False  #: for Cache we need to release the handler mutex to allow RW at the same time


class DocIDCache(BaseCache):
    """Store doc ids in a int64 set and persistent it to a numpy array """

    # TODO temp data structure
    # TODO can we use BinaryPbInd inside this?
    store = {}

    def __init__(self, index_filename: str = None, *args, **kwargs):
        if not index_filename:
            # create a new temp file if not exist
            index_filename = tempfile.NamedTemporaryFile(delete=False).name
        super().__init__(index_filename, *args, **kwargs)

    def add(self, doc_id: UniqueId, *args, **kwargs):
        self._size += 1
        self.store[doc_id] = kwargs.get(DATA_FIELD)

    @deprecated_alias(doc_id='data')
    def query(self, data: UniqueId, *args, **kwargs) -> Optional[bool]:
        """
        @param data: either the `id` or the `content_hash` of a `Document`
        """
        # print(f'query = {data}, self.store = {self.store}')
        status = (data in self.store.values()) or None
        print(f'query = {data}. status = {status}')
        return status

    def get_create_handler(self):
        pass

    def update(self, keys: Iterator[int], values: Iterator[bytes], *args, **kwargs):
        """
        :param keys: list of Document.id
        :param values: list of either `id` or `content_hash` of :class:`Document"""
        missed = check_keys_exist(keys, self.store.keys())
        if missed:
            raise KeyError(f'Keys {missed} were not found. No operation performed...')

        for key, value in zip(keys, values):
            self.store[key] = value

    def delete(self, keys: Iterator[int], *args, **kwargs):
        """
        :param keys: list of Document.id
        """
        missed = check_keys_exist(keys, self.store.keys())
        if missed:
            raise KeyError(f'Keys {missed} were not found. No operation performed...')

        for key in keys:
            del self.store[key]
            self._size -= 1

    def get_add_handler(self):
        pass

    def get_query_handler(self):
        pass
