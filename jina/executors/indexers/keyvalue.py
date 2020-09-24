__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import mmap
from typing import Iterator, Optional

import numpy as np

from . import BaseKVIndexer
from ...proto import jina_pb2


class BasePbIndexer(BaseKVIndexer):
    """Depreciated, just for back-compat and for keeping the inheritance order unchanged"""


class BinaryPbIndexer(BasePbIndexer):
    class FileHandler:
        def __init__(self, path, mode):
            self.body = open(path, mode)
            self.header = open(path + '.head', mode)

        def close(self):
            self.body.close()
            self.header.close()

        def flush(self):
            self.body.flush()
            self.header.flush()

    def get_add_handler(self):
        return self.FileHandler(self.index_abspath, 'ab')

    def get_create_handler(self):
        return self.FileHandler(self.index_abspath, 'wb')

    def get_query_handler(self):
        with open(self.index_abspath + '.head', 'rb') as fp:
            tmp = np.frombuffer(fp.read(), dtype=np.uint64).reshape([-1, 4])
            d = {r[0]: r[1:] for r in tmp}
        return d

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._total_byte_len = 0
        self._page_size = mmap.ALLOCATIONGRANULARITY

    def add(self, docs: Iterator['jina_pb2.Document'], *args, **kwargs):
        _start = 0
        for d in docs:
            s = d.SerializeToString()
            l = len(s)  #: the length
            p = int(_start / self._page_size) * self._page_size  #: offset of the page
            r = _start % self._page_size  #: the reminder, i.e. the start position given the offset
            self.write_handler.header.write(np.array((d.id, p, r, r + l), dtype=np.uint64).tobytes())
            _start += l
            self.write_handler.body.write(s)
            self._size += 1

    def query(self, key: int) -> Optional['jina_pb2.Document']:

        pos_info = self.query_handler.get(key, None)
        if pos_info is not None:
            p, r, l = pos_info
            with open(self.index_abspath, 'r+b') as f, \
                    mmap.mmap(f.fileno(), offset=p, length=l) as m:
                b = jina_pb2.Document()
                b.ParseFromString(m[r:])
                return b


class DataURIPbIndexer(BinaryPbIndexer):
    """Shortcut for :class:`DocPbIndexer` equipped with ``requests.on`` for storing doc-level protobuf and data uri info,
    differ with :class:`ChunkPbIndexer` only in ``requests.on`` """
