__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import mmap
import os
from typing import Iterable, Optional

import numpy as np

from . import BaseKVIndexer
from ..compound import CompoundExecutor

HEADER_NONE_ENTRY = (-1, -1, -1)


class BinaryPbIndexer(BaseKVIndexer):
    """Simple Key-value indexer."""

    class WriteHandler:
        """
        Write file handler.

        :param path: Path of the file.
        :param mode: Writing mode. (e.g. 'ab', 'wb')
        """

        def __init__(self, path, mode):
            self.body = open(path, mode)
            self.header = open(path + '.head', mode)

        def close(self):
            """Close the file."""
            if not self.body.closed:
                self.body.close()
            if not self.header.closed:
                self.header.close()

        def flush(self):
            """Clear the body and header."""
            if not self.body.closed:
                self.body.flush()
            if not self.header.closed:
                self.header.flush()

    class ReadHandler:
        """
        Read file handler.

        :param path: Path of the file.
        :param key_length: Length of key.
        """

        def __init__(self, path, key_length):
            with open(path + '.head', 'rb') as fp:
                tmp = np.frombuffer(
                    fp.read(),
                    dtype=[
                        ('', (np.str_, key_length)),
                        ('', np.int64),
                        ('', np.int64),
                        ('', np.int64),
                    ],
                )
                self.header = {
                    r[0]: None
                    if np.array_equal((r[1], r[2], r[3]), HEADER_NONE_ENTRY)
                    else (r[1], r[2], r[3])
                    for r in tmp
                }
            self._body = open(path, 'r+b')
            self.body = self._body.fileno()

        def close(self):
            """Close the file."""
            if not self._body.closed:
                self._body.close()

    def __getstate__(self):
        # called on pickle save
        if self.delete_on_dump:
            self._delete_invalid_indices()
        d = super().__getstate__()
        return d

    def _delete_invalid_indices(self):
        if self.query_handler:
            self.query_handler.close()
        if self.write_handler:
            self.write_handler.flush()
            self.write_handler.close()

        keys = []
        vals = []
        # we read the valid values and write them to the intermediary file
        read_handler = self.ReadHandler(self.index_abspath, self.key_length)
        for key in read_handler.header.keys():
            pos_info = read_handler.header.get(key, None)
            if pos_info:
                p, r, l = pos_info
                with mmap.mmap(read_handler.body, offset=p, length=l) as m:
                    keys.append(key)
                    vals.append(m[r:])
        read_handler.close()
        if len(keys) == 0:
            return

        # intermediary file
        tmp_file = self.index_abspath + '-tmp'
        self._start = 0
        filtered_data_writer = self.WriteHandler(tmp_file, 'ab')
        # reset size
        self._size = 0
        self._add(keys, vals, filtered_data_writer)
        filtered_data_writer.close()

        # replace orig. file
        # and .head file
        head_path = self.index_abspath + '.head'
        os.remove(self.index_abspath)
        os.remove(head_path)
        os.rename(tmp_file, self.index_abspath)
        os.rename(tmp_file + '.head', head_path)

    def get_add_handler(self) -> 'WriteHandler':
        """
        Get write file handler.

        :return: write handler
        """
        # keep _start position as in pickle serialization
        return self.WriteHandler(self.index_abspath, 'ab')

    def get_create_handler(self) -> 'WriteHandler':
        """
        Get write file handler.

        :return: write handler.
        """
        self._start = 0  # override _start position
        return self.WriteHandler(self.index_abspath, 'wb')

    def get_query_handler(self) -> 'ReadHandler':
        """
        Get read file handler.

        :return: read handler.
        """
        return self.ReadHandler(self.index_abspath, self.key_length)

    def __init__(self, delete_on_dump: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._start = 0
        self._page_size = mmap.ALLOCATIONGRANULARITY
        self.delete_on_dump = delete_on_dump

    def add(
        self, keys: Iterable[str], values: Iterable[bytes], *args, **kwargs
    ) -> None:
        """Add the serialized documents to the index via document ids.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param values: serialized documents
        :param args: extra arguments
        :param kwargs: keyword arguments
        """
        if not any(keys):
            return

        for key, value in zip(keys, values):
            l = len(value)  #: the length
            p = (
                int(self._start / self._page_size) * self._page_size
            )  #: offset of the page
            r = (
                self._start % self._page_size
            )  #: the remainder, i.e. the start position given the offset
            self.write_handler.header.write(
                np.array(
                    (key, p, r, r + l),
                    dtype=[
                        ('', (np.str_, self.key_length)),
                        ('', np.int64),
                        ('', np.int64),
                        ('', np.int64),
                    ],
                ).tobytes()
            )
            self._start += l
            self.write_handler.body.write(value)
            self._size += 1
        self.write_handler.flush()

    def query(self, key: str, *args, **kwargs) -> Optional[bytes]:
        """Find the serialized document to the index via document id.

        :param key: document id
        :param args: extra arguments
        :param kwargs: keyword arguments
        :return: serialized documents
        """
        pos_info = self.query_handler.header.get(key, None)
        if pos_info is not None:
            p, r, l = pos_info
            with mmap.mmap(self.query_handler.body, offset=p, length=l) as m:
                return m[r:]

    def update(
        self, keys: Iterable[str], values: Iterable[bytes], *args, **kwargs
    ) -> None:
        """Update the serialized documents on the index via document ids.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param values: serialized documents
        :param args: extra arguments
        :param kwargs: keyword arguments
        """
        keys, values = self._filter_nonexistent_keys_values(
            keys, values, self.query_handler.header.keys()
        )
        del self.query_handler
        self.handler_mutex = False
        if keys:
            self._delete(keys)
            self.add(keys, values)

    def _delete(self, keys: Iterable[str]) -> None:
        for key in keys:
            self.write_handler.header.write(
                np.array(
                    tuple(np.concatenate([[key], HEADER_NONE_ENTRY])),
                    dtype=[
                        ('', (np.str_, self.key_length)),
                        ('', np.int64),
                        ('', np.int64),
                        ('', np.int64),
                    ],
                ).tobytes()
            )
            self._size -= 1

    def delete(self, keys: Iterable[str], *args, **kwargs) -> None:
        """Delete the serialized documents from the index via document ids.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param args: extra arguments
        :param kwargs: keyword arguments
        """
        keys = self._filter_nonexistent_keys(keys, self.query_handler.header.keys())
        del self.query_handler
        self.handler_mutex = False
        if keys:
            self._delete(keys)

    def _add(self, keys: Iterable[str], values: Iterable[bytes], writer: WriteHandler):
        for key, value in zip(keys, values):
            l = len(value)  #: the length
            p = (
                int(self._start / self._page_size) * self._page_size
            )  #: offset of the page
            r = (
                self._start % self._page_size
            )  #: the remainder, i.e. the start position given the offset
            # noinspection PyTypeChecker
            writer.header.write(
                np.array(
                    (key, p, r, r + l),
                    dtype=[
                        ('', (np.str_, self.key_length)),
                        ('', np.int64),
                        ('', np.int64),
                        ('', np.int64),
                    ],
                ).tobytes()
            )
            self._start += l
            writer.body.write(value)
            self._size += 1
        writer.flush()


class DataURIPbIndexer(BinaryPbIndexer):
    """Alias for BinaryPbIndexer"""


class UniquePbIndexer(CompoundExecutor):
    """A frequently used pattern for combining a :class:`BaseKVIndexer` and a :class:`DocCache` """
