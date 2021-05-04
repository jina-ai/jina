import mmap
import os
from typing import Iterable, Optional, Union

import numpy as np

from . import BaseIndexer

HEADER_NONE_ENTRY = (-1, -1, -1)


class _WriteHandler:
    """
    Write file handler.
    :param path: Path of the file.
    :param mode: Writing mode. (e.g. 'ab', 'wb')
    """

    def __init__(self, path, mode):
        self.path = path
        self.mode = mode
        self.body = open(self.path, self.mode)
        self.header = open(self.path + '.head', self.mode)

    def __enter__(self):
        if self.body.closed:
            self.body = open(self.path, self.mode)
        if self.header.closed:
            self.header = open(self.path + '.head', self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()

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


class _ReadHandler:
    """
    Read file handler.
    :param path: Path of the file.
    :param key_length: Length of key.
    """

    def __init__(self, path, key_length):
        self.path = path
        self.header = {}
        if os.path.exists(self.path + '.head'):
            with open(self.path + '.head', 'rb') as fp:
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
            if os.path.exists(self.path):
                self._body = open(self.path, 'r+b')
                self.body = self._body.fileno()
            else:
                raise FileNotFoundError(
                    f'Path not found {self.path}. Querying will not work'
                )
        else:
            raise FileNotFoundError(
                f'Path not found {self.path + ".head"}. Querying will not work'
            )

    def close(self):
        """Close the file."""
        if hasattr(self, '_body'):
            if not self._body.closed:
                self._body.close()


class _CloseHandler:
    def __init__(self, handler: Union['_WriteHandler', '_ReadHandler']):
        self.handler = handler

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handler is not None:
            self.handler.close()


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
        return _WriteHandler(self.index_abspath, 'ab')

    def get_create_handler(self) -> '_WriteHandler':
        """
        Get write file handler.
        :return: write handler.
        """

        self._start = 0  # override _start position
        return _WriteHandler(self.index_abspath, 'wb')

    def get_query_handler(self) -> '_ReadHandler':
        """
        Get read file handler.
        :return: read handler.
        """
        return _ReadHandler(self.index_abspath, self.key_length)

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

    def _query(self, keys: Iterable[str]):
        query_results = []
        for key in keys:
            pos_info = self.query_handler.header.get(key, None)
            if pos_info is not None:
                p, r, l = pos_info
                with mmap.mmap(self.query_handler.body, offset=p, length=l) as m:
                    query_results.append(m[r:])
            else:
                query_results.append(None)

        return query_results


class KeyValueIndexer(BinaryPbWriterMixin, BaseIndexer):
    """Simple Key-value indexer."""

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

        need_to_remove_handler = not self.is_exist
        with self.write_handler as writer_handler:
            self._add(keys, values, write_handler=writer_handler)
        if need_to_remove_handler:
            # very hacky way to ensure write_handler will use add_handler at next computation, this must be solved
            # by touching file at __init__ time
            del self.write_handler
            self.is_handler_loaded = False

    def query(self, keys: Iterable[str], *args, **kwargs) -> Iterable[Optional[bytes]]:
        """Find the serialized document to the index via document id.
        :param keys: list of document ids
        :param args: extra arguments
        :param kwargs: keyword arguments
        :return: serialized documents
        """
        return self._query(keys)
