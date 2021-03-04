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
    """Simple Key-value indexer that writes to disk

    :param delete_on_dump: whether to delete the entries that were marked as 'deleted'
    """

    class WriteHandler:
        """
        Write file handler.

        :param path: Path of the file.
        :param mode: Writing mode. (e.g. 'ab', 'wb')
        """

        def __init__(self, path, mode):
            self.body = open(path, mode)
            self.header = open(path + '.head', mode)

        def __init__(self, path, mode):
            self.path = path
            self.mode = mode
            print(f'### writehandler mode = {self.mode}')

        def __enter__(self):
            print(f'### WriteHandler enter. mode = {self.mode}, path = {self.path}')
            self.body = open(self.path, self.mode)
            self.header = open(self.path + '.head', self.mode)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._flush()
            self._close()

        def _close(self):
            # TODO do we need to make sure
            self.body.close()
            self.header.close()

        def close(self):
            """Close the file."""
            if getattr(self, 'body', None) and not self.body.closed:
                self.body.flush()
                self.body.close()
            if getattr(self, 'header', None) and not self.header.closed:
                self.header.flush()
                self.header.close()

        def _flush(self):
            """Clear the body and header."""
            self.body.flush()
            self.header.flush()

    class ReadHandler:
        """
        Read file handler.

        :param path: Path of the file.
        :param key_length: Length of key.
        """

        def __init__(self, path, key_length):
            self.path = path
            self.key_length = key_length

        def __enter__(self):
            print(f'### ReadHandler enter. path = {self.path}')
            with open(self.path + '.head', 'rb') as fp:
                tmp = np.frombuffer(
                    fp.read(),
                    dtype=[
                        ('', (np.str_, self.key_length)),
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
            self._body = open(self.path, 'r+b')
            self.body = self._body.fileno()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.header = None
            self._close()
            self.body = None

        def _close(self):
            """Close the file."""
            self._body.close()

    def __getstate__(self):
        # called on pickle save
        if self.delete_on_dump:
            self._delete_invalid_indices()
        d = super().__getstate__()
        return d

    def _delete_invalid_indices(self):
        keys = []
        vals = []
        # we read the valid values and write them to the intermediary file
        with self.ReadHandler(self.index_abspath, self.key_length) as read_handler:
            for key in read_handler.header.keys():
                pos_info = read_handler.header.get(key, None)
                if pos_info:
                    p, r, l = pos_info
                    with mmap.mmap(read_handler.body, offset=p, length=l) as m:
                        keys.append(key)
                        vals.append(m[r:])
        if len(keys) == 0:
            return

        # intermediary file
        tmp_file = self.index_abspath + '-tmp'
        self._start = 0
        # reset size
        self._size = 0
        with self.WriteHandler(tmp_file, 'ab') as filtered_data_writer:
            self._add(keys, vals, filtered_data_writer)

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
        # keep _start position as in pickle serializ`ation
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
        print(f'### add: len(keys) = {len(keys)}, len(values) = {len(values)}')
        if not len(keys):
            return

        with self.get_add_handler() as writer:
            self._add(keys, values, writer=writer)
        print(f'### end of add: size = {self.size}')

    def query(self, key: str) -> Optional[bytes]:
        """Find the serialized document to the index via document id.

        :param key: document id
        :return: serialized documents
        """
        if self.size == 0:
            return

        with self.ReadHandler(self.index_abspath, self.key_length) as reader:
            pos_info = reader.header.get(key, None)
            if pos_info is not None:
                p, r, l = pos_info
                with mmap.mmap(reader.body, offset=p, length=l) as m:
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
        with self.query_handler as reader:
            keys, values = self._filter_nonexistent_keys_values(
                keys, values, reader.header.keys()
            )

        if len(keys):
            self._delete(keys)
            self.add(keys, values)

    def _delete(self, keys: Iterable[str]) -> None:
        print(f'### _delete: len(keys) = {len(keys)}')
        if self.size == 0:
            self.logger.warning(
                f'Delete operation on empty BinaryPbIndexer at {self.index_abspath}'
            )

        with self.get_add_handler() as writer:
            for key in keys:
                # noinspection PyTypeChecker
                writer.header.write(
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
        with self.query_handler as reader:
            keys = self._filter_nonexistent_keys(keys, reader.header.keys())

        if keys:
            self._delete(keys)
        print(f'### end of delete: size = {self.size}')

    def _add(self, keys: Iterable[str], values: Iterable[bytes], writer: WriteHandler):
        print(f'### _add: len(keys) = {len(keys)}, len(values) = {len(values)}')
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
        print(f'### end of _add: size = {self.size}')

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
        writer._flush()


class DataURIPbIndexer(BinaryPbIndexer):
    """Alias for BinaryPbIndexer"""


class UniquePbIndexer(CompoundExecutor):
    """A frequently used pattern for combining a :class:`BaseKVIndexer` and a :class:`DocCache` """
