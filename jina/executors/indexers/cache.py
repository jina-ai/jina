"""Indexer for caching."""

import pickle
import tempfile
from typing import Optional, Iterable

from jina.executors.indexers import BaseKVIndexer

DATA_FIELD = 'data'
ID_KEY = 'id'
CONTENT_HASH_KEY = 'content_hash'


class BaseCache(BaseKVIndexer):
    """Base class of the cache inherited :class:`BaseKVIndexer`.

    The difference between a cache and a :class:`BaseKVIndexer` is the ``handler_mutex`` is released in cache,
    this allows one to query-while-indexing.
    """

    def __init__(self, *args, **kwargs):
        """Create a new BaseCache."""
        super().__init__(*args, **kwargs)

    def post_init(self):
        """For Cache we need to release the handler mutex to allow RW at the same time."""
        self.handler_mutex = False


class DocCache(BaseCache):
    """A key-value indexer that specializes in caching.

    Serializes the cache to two files, one for ids, one for the actually cached field.
    If field=`id`, then the second file is redundant. The class optimizes the process
    so that there are no duplicates.
    """

    class CacheHandler:
        """A handler for loading and serializing the in-memory cache of the DocCache."""

        def __init__(self, path, logger):
            """Create a new CacheHandler.

            :param path: Path to the file from which to build the actual paths.
            :param logger: Instance of logger.
            """
            self.path = path
            try:
                self.id_to_cache_val = pickle.load(open(path + '.ids', 'rb'))
                self.cache_val_to_id = pickle.load(open(path + '.cache', 'rb'))
            except FileNotFoundError as e:
                logger.warning(
                    f'File path did not exist : {path}.ids or {path}.cache: {e!r}. Creating new CacheHandler...')
                self.id_to_cache_val = dict()
                self.cache_val_to_id = dict()

        def close(self):
            """Flushes the in-memory cache to pickle files."""
            pickle.dump(self.id_to_cache_val, open(self.path + '.ids', 'wb'))
            pickle.dump(self.cache_val_to_id, open(self.path + '.cache', 'wb'))

    supported_fields = [ID_KEY, CONTENT_HASH_KEY]
    default_field = ID_KEY

    def __init__(self, index_filename: Optional[str] = None, field: Optional[str] = None, *args, **kwargs):
        """Create a new DocCache.

        :param index_filename: file name for storing the cache data
        :param field: field to cache on (ID_KEY or CONTENT_HASH_KEY)
        """
        if not index_filename:
            # create a new temp file if not exist
            index_filename = tempfile.NamedTemporaryFile(delete=False).name
        super().__init__(index_filename, *args, **kwargs)
        self.field = field or self.default_field
        if self.field not in self.supported_fields:
            raise ValueError(f"Field '{self.field}' not in supported list of {self.supported_fields}")

    def add(self, keys: Iterable[str], values: Iterable[str], *args, **kwargs) -> None:
        """Add a document to the cache depending.

        :param keys: document ids to be added
        :param values: document cache values to be added
        """
        for key, value in zip(keys, values):
            self.query_handler.id_to_cache_val[key] = value
            self.query_handler.cache_val_to_id[value] = key
            self._size += 1

    def query(self, key: str, *args, **kwargs) -> bool:
        """Check whether the data exists in the cache.

        :param key: either the id or the content_hash of a Document
        :return: status
        """
        return key in self.query_handler.cache_val_to_id

    def update(self, keys: Iterable[str], values: Iterable[str], *args, **kwargs) -> None:
        """Update cached documents.

        :param keys: list of Document.id
        :param values: list of either `id` or `content_hash` of :class:`Document`
        """
        # if we don't cache anything else, no need
        if self.field != ID_KEY:
            for key, value in zip(keys, values):
                if key not in self.query_handler.id_to_cache_val:
                    continue
                old_value = self.query_handler.id_to_cache_val[key]
                self.query_handler.id_to_cache_val[key] = value
                del self.query_handler.cache_val_to_id[old_value]
                self.query_handler.cache_val_to_id[value] = key

    def delete(self, keys: Iterable[str], *args, **kwargs) -> None:
        """Delete documents from the cache.

        :param keys: list of Document.id
        """
        for key in keys:
            if key not in self.query_handler.id_to_cache_val:
                continue
            value = self.query_handler.id_to_cache_val[key]
            del self.query_handler.id_to_cache_val[key]
            del self.query_handler.cache_val_to_id[value]
            self._size -= 1

    def get_add_handler(self):
        """Get the CacheHandler."""
        return self.get_query_handler()

    def get_query_handler(self) -> CacheHandler:
        """Get the CacheHandler."""
        return self.CacheHandler(self.save_abspath, self.logger)

    def get_create_handler(self):
        """Get the CacheHandler."""
        return self.get_query_handler()
