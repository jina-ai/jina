__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import mmap
import os
import random
from typing import Iterable, Optional

import numpy as np

from . import BaseKVIndexer
from ..compound import CompoundExecutor
from ...logging import JinaLogger

HEADER_NONE_ENTRY = (-1, -1, -1)


class _WriteHandler:
    """
    Write file handler.

    :param path: Path of the file.
    :param mode: Writing mode. (e.g. 'ab', 'wb')
    """

    def __init__(self, path, mode, logger):

        self.logger = logger
        self.path = path
        self.mode = mode
        self.logger.warning(f'WRITEHANDLER CREATE {self.path} with mode {self.mode}')

    def __enter__(self):
        self.logger.warning(f'WRITEHANDLER ENTER {self.path} with mode {self.mode}')
        self.body = open(self.path, self.mode)
        self.header = open(self.path + '.head', self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()
        self.close()

    def close(self):
        """Close the file."""
        self.logger.warning(f'WRITEHANDLER CLOSHHHHHHHHHHHHH {self.path}')

        if hasattr(self, 'body'):
            self.logger.warning(f'WRITEHANDLER CLOSE {self.body}')

            if not self.body.closed:
                self.body.close()
        if hasattr(self, 'header'):
            if not self.header.closed:
                self.header.close()

    def flush(self):
        """Clear the body and header."""
        self.logger.warning(f'WRITEHANDLER FLUSHHHHHHHHHHHHH {self.path}')
        self.logger.warning(f' before size {os.path.getsize(self.path)}')

        if hasattr(self, 'body'):
            self.logger.warning(f' WRITEHANDLER FLUSH {self.body}')
            if not self.body.closed:
                self.body.flush()
        if hasattr(self, 'header'):
            if not self.header.closed:
                self.header.flush()
        self.logger.warning(f' size {os.path.getsize(self.path)}')


class _ReadHandler:
    """
    Read file handler.

    :param path: Path of the file.
    :param key_length: Length of key.
    """

    def __init__(self, path, key_length, logger):
        self.logger = logger
        self.path = path
        self.key_length = key_length
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

    def __enter__(self):
        self._body = open(self.path, 'r+b')
        self.body = self._body.fileno()
        self.logger.warning(f' READHANDLER self.path {self.path} => {self.body}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the file."""
        if hasattr(self, '_body'):
            if not self._body.closed:
                self._body.close()


class BinaryPbWriterMixin:
    """Mixing for providing the binarypb writing and reading methods"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._start = 0
        self._page_size = mmap.ALLOCATIONGRANULARITY

    def get_add_handler(self) -> '_WriteHandler':
        """
        Get write file handler.

        :return: write handler
        """
        # keep _start position as in pickle serialization
        self.logger.warning(f' get_add_handler self start to keep {self._start}')
        return _WriteHandler(self.index_abspath, 'ab', self.logger)

    def get_create_handler(self) -> '_WriteHandler':
        """
        Get write file handler.

        :return: write handler.
        """
        self._start = 0  # override _start position
        return _WriteHandler(self.index_abspath, 'wb', self.logger)

    def get_query_handler(self) -> '_ReadHandler':
        """
        Get read file handler.

        :return: read handler.
        """
        return _ReadHandler(self.index_abspath, self.key_length, self.logger)

    def _add(
        self, keys: Iterable[str], values: Iterable[bytes], write_handler: _WriteHandler
    ):
        for key, value in zip(keys, values):
            l = len(value)  #: the length
            p = (
                int(self._start / self._page_size) * self._page_size
            )  #: offset of the page
            r = (
                self._start % self._page_size
            )  #: the remainder, i.e. the start position given the offset
            # noinspection PyTypeChecker
            write_handler.header.write(
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
            write_handler.body.write(value)
            self._size += 1

    def delete(self, keys: Iterable[str], *args, **kwargs) -> None:
        """Delete the serialized documents from the index via document ids.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param args: not used
        :param kwargs: not used
        """
        keys = self._filter_nonexistent_keys(keys, self.query_handler.header.keys())
        del self.query_handler
        self.handler_mutex = False
        if keys:
            self._delete(keys)

    def _delete(self, keys: Iterable[str]) -> None:
        with self.write_handler as write_handler:
            for key in keys:
                write_handler.header.write(
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

    def _query(self, key):
        self.logger.warning(f' key {key}')
        pos_info = self.query_handler.header.get(key, None)

        with self.query_handler as query_handler:

            if pos_info is not None:
                p, r, l = pos_info
                self.logger.warning(f' p, r, l {p}, {r}, {l}')
                self.logger.warning(f' start {self._start}')
                self.logger.warning(f' query_handler.body {query_handler.body}')
                self.logger.warning(f' type(body) {type(query_handler.body)}')
                self.logger.warning(f' size {os.path.getsize(query_handler.path)}')

                with mmap.mmap(query_handler.body, offset=p, length=l) as m:
                    return m[r:]


class BinaryPbIndexer(BinaryPbWriterMixin, BaseKVIndexer):
    """Simple Key-value indexer."""

    def __init__(self, delete_on_dump: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delete_on_dump = delete_on_dump

    def __getstate__(self):
        # called on pickle save
        if self.delete_on_dump:
            self._delete_invalid_indices()
        d = super().__getstate__()
        self.logger.warning(f' start {d["_start"]}')
        return d

    def _delete_invalid_indices(self):
        keys = []
        vals = []
        # we read the valid values and write them to the intermediary file
        with _ReadHandler(self.index_abspath, self.key_length) as read_handler:
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
        filtered_data_writer = _WriteHandler(tmp_file, 'ab')
        with filtered_data_writer:
            # reset size
            self._size = 0
            self._add(keys, vals, write_handler=filtered_data_writer)

        # replace orig. file
        # and .head file
        head_path = self.index_abspath + '.head'
        os.remove(self.index_abspath)
        os.remove(head_path)
        os.rename(tmp_file, self.index_abspath)
        os.rename(tmp_file + '.head', head_path)

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

        with self.write_handler as writer_handler:
            self._add(keys, values, write_handler=writer_handler)

    def sample(self) -> Optional[bytes]:
        """Return a random entry from the indexer for sanity check.

        :return: A random entry from the indexer.
        """
        k = random.sample(self.query_handler.header.keys(), k=1)[0]
        return self[k]

    def __iter__(self):
        for k in self.query_handler.header.keys():
            yield self[k]

    def query(self, key: str, *args, **kwargs) -> Optional[bytes]:
        """Find the serialized document to the index via document id.

        :param key: document id
        :param args: extra arguments
        :param kwargs: keyword arguments
        :return: serialized documents
        """
        return self._query(key)

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

    def delete(self, keys: Iterable[str], *args, **kwargs) -> None:
        """Delete the serialized documents from the index via document ids.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param args: not used
        :param kwargs: not used"""
        super(BinaryPbIndexer, self).delete(keys)


class KeyValueIndexer(BinaryPbIndexer):
    """Alias for :class:`BinaryPbIndexer` """


class DataURIPbIndexer(BinaryPbIndexer):
    """Alias for BinaryPbIndexer"""


class UniquePbIndexer(CompoundExecutor):
    """A frequently used pattern for combining a :class:`BaseKVIndexer` and a :class:`DocCache` """
