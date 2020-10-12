from typing import Optional

import numpy as np

from . import BaseKVIndexer
from ...proto import uid


class DocIDCache(BaseKVIndexer):
    """Store doc ids in a int64 set and persistent it to a numpy array """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.handler_mutex = False  #: for Cache we need to release the handler mutex to allow RW at the same time

    def add(self, doc_id: str, *args, **kwargs):
        d_id = uid.id2hash(doc_id)
        self.query_handler.add(d_id)
        self._size += 1
        self.write_handler.write(np.int64(d_id).tobytes())

    def query(self, doc_id: str, *args, **kwargs) -> Optional[bool]:
        if self.query_handler:
            d_id = uid.id2hash(doc_id)
            return (d_id in self.query_handler) or None

    @property
    def is_exist(self) -> bool:
        """ Always return true, delegate to :meth:`get_query_handler`

        :return: True
        """
        return True

    def get_query_handler(self):
        if super().is_exist:
            with open(self.index_abspath, 'rb') as fp:
                return set(np.frombuffer(fp.read(), dtype=np.int64))
        else:
            return set()

    def get_add_handler(self):
        return open(self.index_abspath, 'ab')

    def get_create_handler(self):
        return open(self.index_abspath, 'wb')
