import tempfile
from typing import Optional, Iterator

from jina.executors.indexers import BaseKVIndexer
from jina.helper import deprecated_alias, check_keys_exist

DATA_FIELD = 'data'
ID_KEY = 'id'
CONTENT_HASH_KEY = 'content_hash'


class BaseCache(BaseKVIndexer):
    """Base class of the cache inherited :class:`BaseKVIndexer`

    The difference between a cache and a :class:`BaseKVIndexer` is the ``handler_mutex`` is released in cache, this allows one to query-while-indexing.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_init(self):
        self.handler_mutex = False  #: for Cache we need to release the handler mutex to allow RW at the same time


class DocIDCache(BaseCache):
    """..."""
    # TODO docs

    # TODO temp data structure
    store = {}
    supported_fields = [ID_KEY, CONTENT_HASH_KEY]
    default_field = ID_KEY

    def __init__(self, index_filename: str = None, *args, **kwargs):
        if not index_filename:
            # create a new temp file if not exist
            index_filename = tempfile.NamedTemporaryFile(delete=False).name
        super().__init__(index_filename, *args, **kwargs)
        self.store = {}
        self.field = kwargs.get('field', self.default_field)
        # TODO optimization in case it's just id
        if self.field not in self.supported_fields:
            raise ValueError(f"Field '{self.field}' not in supported list of {self.supported_fields}")

    @deprecated_alias(doc_id='doc')
    def add(self, doc: 'Document', *args, **kwargs):
        cached_field = doc.id
        if self.field == CONTENT_HASH_KEY:
            cached_field = doc.content_hash
        self._size += 1
        self.store[doc.id] = cached_field

    @deprecated_alias(doc_id='doc')
    def query(self, doc: 'Document', *args, **kwargs) -> Optional[bool]:
        """
        Check whether the given doc's cached field exists in the index

        @param doc: the 'Document' you want to query for
        """
        cached_field = doc.id
        if self.field == CONTENT_HASH_KEY:
            cached_field = doc.content_hash
        status = (cached_field in self.store.values()) or None
        # FIXME cleanup
        print(f'query = {cached_field}. status = {status}')
        return status

    def update(self, keys: Iterator[int], values: Iterator['Document'], *args, **kwargs):
        """
        :param keys: list of 'Document'.id
        :param values: list of either `id` or `content_hash` of :class:`'Document'"""
        missed = check_keys_exist(keys, self.store.keys())
        if missed:
            raise KeyError(f'Keys {missed} were not found. No operation performed...')

        for key, doc in zip(keys, values):
            cached_field = doc.id
            if self.field == CONTENT_HASH_KEY:
                cached_field = doc.content_hash
            self.store[key] = cached_field

    def delete(self, keys: Iterator[int], *args, **kwargs):
        """
        :param keys: list of 'Document'.id
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

    def get_create_handler(self):
        pass
