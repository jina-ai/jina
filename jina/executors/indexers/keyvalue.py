__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import mmap
from typing import Iterator, Optional

import numpy as np

from . import BaseKVIndexer
from ...proto import jina_pb2, uid


class BinaryPbIndexer(BaseKVIndexer):
    class WriteHandler:
        def __init__(self, path, mode):
            self.body = open(path, mode)
            self.header = open(path + '.head', mode)

        def close(self):
            self.body.close()
            self.header.close()

        def flush(self):
            self.body.flush()
            self.header.flush()

    class ReadHandler:
        def __init__(self, path):
            with open(path + '.head', 'rb') as fp:
                tmp = np.frombuffer(fp.read(), dtype=np.int64).reshape([-1, 4])
                self.header = {r[0]: r[1:] for r in tmp}
            self._body = open(path, 'r+b')
            self.body = self._body.fileno()

        def close(self):
            self._body.close()

    def get_add_handler(self):
        # keep _start position as in pickle serialization
        return self.WriteHandler(self.index_abspath, 'ab')

    def get_create_handler(self):
        self._start = 0  # override _start position
        return self.WriteHandler(self.index_abspath, 'wb')

    def get_query_handler(self):
        return self.ReadHandler(self.index_abspath)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._total_byte_len = 0
        self._start = 0
        self._page_size = mmap.ALLOCATIONGRANULARITY

    def add(self, docs: Iterator['jina_pb2.Document'], *args, **kwargs):
        for d in docs:
            s = d.SerializeToString()
            l = len(s)  #: the length
            p = int(self._start / self._page_size) * self._page_size  #: offset of the page
            r = self._start % self._page_size  #: the reminder, i.e. the start position given the offset
            self.write_handler.header.write(np.array((uid.id2hash(d.id), p, r, r + l), dtype=np.int64).tobytes())
            self._start += l
            self.write_handler.body.write(s)
            self._size += 1
            # print(f'l: {l} p: {p} r: {r} r+l: {r + l} size: {self._size}')

    def query(self, key: int) -> Optional['jina_pb2.Document']:
        # print(f'key={key}')
        pos_info = self.query_handler.header.get(key, None)
        if pos_info is not None:
            p, r, l = pos_info
            with mmap.mmap(self.query_handler.body, offset=p, length=l) as m:
                # print(f'{p}\t{r}\t{l}')
                b = jina_pb2.Document()
                b.ParseFromString(m[r:])
                # print(b)
                return b


class DataURIPbIndexer(BinaryPbIndexer):
    """Shortcut for :class:`DocPbIndexer` equipped with ``requests.on`` for storing doc-level protobuf and data uri info,
    differ with :class:`ChunkPbIndexer` only in ``requests.on`` """
