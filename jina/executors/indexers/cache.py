import pickle
import tempfile
from typing import Optional, Iterator

from jina.executors.indexers import BaseKVIndexer
from jina.helper import deprecated_alias, check_keys_exist

DATA_FIELD = 'data'
ID_KEY = 'id'
CONTENT_HASH_KEY = 'content_hash'

# noinspection PyUnreachableCode
if False:
    from jina.types.document import UniqueId
    from jina import Document


class BaseCache(BaseKVIndexer):
    """Base class of the cache inherited :class:`BaseKVIndexer`

    The difference between a cache and a :class:`BaseKVIndexer` is the ``handler_mutex`` is released in cache, this allows one to query-while-indexing.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_init(self):
        self.handler_mutex = False  #: for Cache we need to release the handler mutex to allow RW at the same time


class DocIDCache(BaseCache):
    """A key-value indexer that specializes in caching.
    Serializes the cache to file
    """

    class CacheHandler:
        def __init__(self, path, logger):
            self.path = path
            try:
                # TODO maybe mmap?
                self.ids = pickle.load(open(path + '.ids', 'rb'))
                self.cache = pickle.load(open(path + '.cache', 'rb'))
            except FileNotFoundError as e:
                logger.warning(
                    f'File path did not exist : {path}.ids or {path}.cache: {repr(e)}. Creating new CacheHandler...')
                self.ids = []
                self.cache = []

        def close(self):
            pickle.dump(self.ids, open(self.path + '.ids', 'wb'))
            pickle.dump(self.cache, open(self.path + '.cache', 'wb'))

    supported_fields = [ID_KEY, CONTENT_HASH_KEY]
    default_field = ID_KEY

    def __init__(self, index_filename: str = None, *args, **kwargs):
        """ creates a new DocIDCache

        :param field: to be passed as kwarg. This dictates by which Document field we cache (either `id` or `content_hash`)
        """
        if not index_filename:
            # create a new temp file if not exist
            index_filename = tempfile.NamedTemporaryFile(delete=False).name
        super().__init__(index_filename, *args, **kwargs)
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
        self.query_handler.ids.append(doc.id)
        self.query_handler.cache.append(cached_field)

    @deprecated_alias(doc_id='doc')
    def query(self, doc: 'Document', *args, **kwargs) -> Optional[bool]:
        """
        Check whether the given doc's cached field exists in the index

        :param doc: the Document you want to query for
        """
        # FIXME
        if self.query_handler is None:
            self.query_handler = self.get_query_handler()
        cached_field = doc.id
        if self.field == CONTENT_HASH_KEY:
            cached_field = doc.content_hash
        status = (cached_field in self.query_handler.cache) or None
        return status

    def update(self, keys: Iterator['UniqueId'], values: Iterator['Document'], *args, **kwargs):
        """
        :param keys: list of Document.id
        :param values: list of either `id` or `content_hash` of :class:`Document"""
        missed = check_keys_exist(keys, self.query_handler.ids)
        if missed:
            raise KeyError(f'Keys {missed} were not found in {self.index_abspath}. No operation performed...')

        for key, doc in zip(keys, values):
            key_idx = self.query_handler.ids.index(key)
            cached_field = doc.id
            if self.field == CONTENT_HASH_KEY:
                cached_field = doc.content_hash
            self.query_handler.cache[key_idx] = cached_field

    def delete(self, keys: Iterator['UniqueId'], *args, **kwargs):
        """
        :param keys: list of Document.id
        """
        missed = check_keys_exist(keys, self.query_handler.ids)
        if missed:
            raise KeyError(f'Keys {missed} were not found in {self.index_abspath}. No operation performed...')

        for key in keys:
            key_idx = self.query_handler.ids.index(key)
            self.query_handler.ids = [id for idx, id in enumerate(self.query_handler.ids) if idx != key_idx]
            self.query_handler.cache = [cache for idx, cache in enumerate(self.query_handler.cache) if idx != key_idx]
            self._size -= 1

    def get_add_handler(self):
        pass

    def get_query_handler(self) -> CacheHandler:
        return self.CacheHandler(self.index_abspath, self.logger)

    def get_create_handler(self):
        pass
