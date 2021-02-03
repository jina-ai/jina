__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import mmap
from typing import Iterable, Optional

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
        def __init__(self, path, key_length):
            with open(path + '.head', 'rb') as fp:
                tmp = np.frombuffer(fp.read(),
                                    dtype=[('', (np.str_, key_length)), ('', np.int64), ('', np.int64), ('', np.int64)])
                self.header = {
                    r[0]: None if np.array_equal((r[1], r[2], r[3]), HEADER_NONE_ENTRY) else (r[1], r[2], r[3]) for r in
                    tmp}
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
        return self.ReadHandler(self.index_abspath, self._key_length)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._total_byte_len = 0
        self._start = 0
        self._page_size = mmap.ALLOCATIONGRANULARITY
        self._key_length = 0

    def add(self, keys: Iterable[str], values: Iterable[bytes], *args, **kwargs):
        """Add the serialized documents to the index via document ids.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param values: serialized documents
        """
        if not keys:
            return

        max_key_len = max([len(k) for k in keys])
        self.key_length = max_key_len

        for key, value in zip(keys, values):
            l = len(value)  #: the length
            p = int(self._start / self._page_size) * self._page_size  #: offset of the page
            r = self._start % self._page_size  #: the remainder, i.e. the start position given the offset
            self.write_handler.header.write(
                np.array(
                    (key, p, r, r + l),
                    dtype=[('', (np.str_, self._key_length)), ('', np.int64), ('', np.int64), ('', np.int64)]
                ).tobytes()
            )
            self._start += l
            self.write_handler.body.write(value)
            self._size += 1
        self.write_handler.flush()

    def query(self, key: str) -> Optional[bytes]:
        """Find the serialized document to the index via document id.

        :param key: document id
        :return: serialized documents
        """
        pos_info = self.query_handler.header.get(key, None)
        if pos_info is not None:
            p, r, l = pos_info
            with mmap.mmap(self.query_handler.body, offset=p, length=l) as m:
                return m[r:]

    def update(self, keys: Iterable[str], values: Iterable[bytes], *args, **kwargs):
        """Update the serialized documents on the index via document ids.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param values: serialized documents
        """
        keys, values = self._filter_nonexistent_keys_values(keys, values, self.query_handler.header.keys(),
                                                            self.save_abspath)
        self._delete(keys)
        self.add(keys, values)

    def _delete(self, keys: Iterable[str]):
        self.query_handler.close()
        self.handler_mutex = False
        for key in keys:
            self.write_handler.header.write(
                np.array(
                    tuple(np.concatenate([[key], HEADER_NONE_ENTRY])),
                    dtype=[('', (np.str_, self._key_length)), ('', np.int64), ('', np.int64), ('', np.int64)]
                ).tobytes()
            )

            if self.query_handler:
                del self.query_handler.header[key]
            self._size -= 1

    def delete(self, keys: Iterable[str], *args, **kwargs):
        """Delete the serialized documents from the index via document ids.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        """
        keys = self._filter_nonexistent_keys(keys, self.query_handler.header.keys(), self.save_abspath)
        self._delete(keys)


class DataURIPbIndexer(BinaryPbIndexer):
    """Alias for BinaryPbIndexer"""


class UniquePbIndexer(CompoundExecutor):
    """A frequently used pattern for combining a :class:`BaseKVIndexer` and a :class:`DocCache` """
