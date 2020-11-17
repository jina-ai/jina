import tempfile
from typing import Optional

import numpy as np

from . import BaseKVIndexer
from ...helper import cached_property
from ...types.document import uid


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

    def __init__(self, index_filename: str = None, *args, **kwargs):
        if not index_filename:
            # create a new temp file if not exist
            index_filename = tempfile.NamedTemporaryFile(delete=False).name
        super().__init__(index_filename, *args, **kwargs)

    def add(self, doc_id: str, *args, **kwargs):
        d_id = uid.id2hash(doc_id)
        self.query_handler.add(d_id)
        self._size += 1
        self.write_handler.write(np.int64(d_id).tobytes())

    def query(self, doc_id: str, *args, **kwargs) -> Optional[bool]:
        d_id = uid.id2hash(doc_id)
        return (d_id in self.query_handler) or None

    def get_query_handler(self):
        with open(self.index_abspath, 'rb') as fp:
            return set(np.frombuffer(fp.read(), dtype=np.int64))

    @cached_property
    def null_query_handler(self):
        """The empty query handler when :meth:`get_query_handler` fails"""
        return set()

    def get_add_handler(self):
        return open(self.index_abspath, 'ab')

    def get_create_handler(self):
        return open(self.index_abspath, 'wb')
