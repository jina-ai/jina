import pickle
import tempfile
from typing import Optional, Iterator

from jina.executors.indexers import BaseKVIndexer

DATA_FIELD = 'data'
ID_KEY = 'id'
CONTENT_HASH_KEY = 'content_hash'

# noinspection PyUnreachableCode
if False:
    from jina.types.document import UniqueId


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
    Serializes the cache to two files, one for ids, one for the actually cached field.
    If field=`id`, then the second file is redundant. The class optimizes the process
    so that there are no duplicates.
    """

    class CacheHandler:
        def __init__(self, path, logger):
            self.path = path
            try:
                # TODO maybe mmap?
                self.ids = pickle.load(open(path + '.ids', 'rb'))
                self.content_hash = pickle.load(open(path + '.cache', 'rb'))
            except FileNotFoundError as e:
                logger.warning(
                    f'File path did not exist : {path}.ids or {path}.cache: {e!r}. Creating new CacheHandler...')
                self.ids = []
                self.content_hash = []

        def close(self):
            pickle.dump(self.ids, open(self.path + '.ids', 'wb'))
            pickle.dump(self.content_hash, open(self.path + '.cache', 'wb'))

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
        if self.field not in self.supported_fields:
            raise ValueError(f"Field '{self.field}' not in supported list of {self.supported_fields}")

    def add(self, doc_id: 'UniqueId', *args, **kwargs):
        self.query_handler.ids.append(doc_id)

        # optimization. don't duplicate ids
        if self.field != ID_KEY:
            data = kwargs.get(DATA_FIELD, None)
            if data is None:
                raise ValueError(f'Got None from CacheDriver')
            self.query_handler.content_hash.append(data)
        self._size += 1

    def query(self, data, *args, **kwargs) -> Optional[bool]:
        """
        Check whether the data exists in the cache

        :param data: either the id or the content_hash of a Document
        """
        # FIXME this shouldn't happen
        if self.query_handler is None:
            self.query_handler = self.get_query_handler()

        if self.field == ID_KEY:
            status = (data in self.query_handler.ids) or None
        else:
            status = (data in self.query_handler.content_hash) or None

        return status

    def update(self, keys: Iterator['UniqueId'], values: Iterator[any], *args, **kwargs):
        """
        :param keys: list of Document.id
        :param values: list of either `id` or `content_hash` of :class:`Document"""
        # if we don't cache anything else, no need
        if self.field != ID_KEY:
            keys, values = self._filter_nonexistent_keys_values(keys, values, self.query_handler.ids, self.save_abspath)

            for key, cached_field in zip(keys, values):
                key_idx = self.query_handler.ids.index(key)
                # optimization. don't duplicate ids
                if self.field != ID_KEY:
                    self.query_handler.content_hash[key_idx] = cached_field

    def delete(self, keys: Iterator['UniqueId'], *args, **kwargs):
        """
        :param keys: list of Document.id
        """
        keys = self._filter_nonexistent_keys(keys, self.query_handler.ids, self.save_abspath)

        for key in keys:
            key_idx = self.query_handler.ids.index(key)
            self.query_handler.ids = [query_id for idx, query_id in enumerate(self.query_handler.ids) if idx != key_idx]
            if self.field != ID_KEY:
                self.query_handler.content_hash = [cached_field for idx, cached_field in
                                                   enumerate(self.query_handler.content_hash) if idx != key_idx]
            self._size -= 1

    def get_add_handler(self):
        # not needed, as we use the queryhandler
        # FIXME better way to silence warnings
        return 1

    def get_query_handler(self) -> CacheHandler:
        return self.CacheHandler(self.index_abspath, self.logger)

    def get_create_handler(self):
        # not needed, as we use the queryhandler
        # FIXME better way to silence warnings
        return 1
