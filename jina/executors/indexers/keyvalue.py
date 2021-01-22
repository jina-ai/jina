__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import mmap
from typing import Iterator, Optional

import numpy as np

from . import BaseKVIndexer
from ..compound import CompoundExecutor

HEADER_NONE_ENTRY = (-1, -1, -1)


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
                self.header = {r[0]: None if np.array_equal(r[1:], HEADER_NONE_ENTRY) else r[1:] for r in tmp}
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

    def add(self, keys: Iterator[int], values: Iterator[bytes], *args, **kwargs):
        if len(list(keys)) != len(list(values)):
            raise ValueError(f'Len of keys {len(keys)} did not match len of values {len(values)}')
        for key, value in zip(keys, values):
            l = len(value)  #: the length
            p = int(self._start / self._page_size) * self._page_size  #: offset of the page
            r = self._start % self._page_size  #: the remainder, i.e. the start position given the offset
            self.write_handler.header.write(
                np.array(
                    (key, p, r, r + l),
                    dtype=np.int64
                ).tobytes()
            )
            self._start += l
            self.write_handler.body.write(value)
            self._size += 1
        self.write_handler.flush()

    def query(self, key: int) -> Optional[bytes]:
        pos_info = self.query_handler.header.get(key, None)
        if pos_info is not None:
            p, r, l = pos_info
            with mmap.mmap(self.query_handler.body, offset=p, length=l) as m:
                return m[r:]

    def update(self, keys: Iterator[int], values: Iterator[bytes], *args, **kwargs):
        keys, values = self._filter_nonexistent_keys_values(keys, values, self.query_handler.header.keys(), self.save_abspath)
        self._delete(keys)
        self.add(keys, values)
        return

    def _delete(self, keys: Iterator[int]):
        self.query_handler.close()
        self.handler_mutex = False
        for key in keys:
            self.write_handler.header.write(
                np.array(
                    np.concatenate([[key], HEADER_NONE_ENTRY]),
                    dtype=np.int64
                ).tobytes()
            )
            if self.query_handler:
                del self.query_handler.header[key]
            self._size -= 1

    def delete(self, keys: Iterator[int], *args, **kwargs):
        keys = self._filter_nonexistent_keys(keys, self.query_handler.header.keys(), self.save_abspath)
        self._delete(keys)


class DataURIPbIndexer(BinaryPbIndexer):
    """Shortcut for :class:`DocPbIndexer` equipped with ``requests.on`` for storing doc-level protobuf and data uri info,
    differ with :class:`ChunkPbIndexer` only in ``requests.on`` """


class UniquePbIndexer(CompoundExecutor):
    """A frequently used pattern for combining a :class:`BaseKVIndexer` and a :class:`DocIDCache` """
