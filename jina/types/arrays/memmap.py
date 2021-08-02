import itertools
import mmap
import os
import shutil
import tempfile
from collections.abc import Iterable as Itr
from pathlib import Path
from typing import (
    Union,
    Iterable,
    Iterator,
)

import numpy as np

from .document import DocumentArrayGetAttrMixin
from .search_ops import DocumentArraySearchOpsMixin
from .traversable import TraversableSequence
from ..document import Document

HEADER_NONE_ENTRY = (-1, -1, -1)
PAGE_SIZE = mmap.ALLOCATIONGRANULARITY


class DocumentArrayMemmap(
    TraversableSequence, DocumentArrayGetAttrMixin, DocumentArraySearchOpsMixin, Itr
):
    """
    Create a memory-map to an :class:`DocumentArray` stored in binary files on disk.

    Memory-mapped files are used for accessing :class:`Document` of large :class:`DocumentArray` on disk,
    without reading the entire file into memory.

    The :class:`DocumentArrayMemmap` on-disk storage consists of two files:
        - `header.bin`: stores id, offset, length and boundary info of each Document in `body.bin`;
        - `body.bin`: stores Documents continuously

    When loading :class:`DocumentArrayMemmap`, it only loads the content of `header.bin` into memory, while storing
    all `body.bin` data on disk. As `header.bin` is often much smaller than `body.bin`, memory is saved.

    This class is designed to work similarly as :class:`DocumentArray` but differs in the following aspects:
        - one can not set the attribute of elements in a :class:`DocumentArrayMemmap`;
        - one can not use slice to index elements in a :class:`DocumentArrayMemmap`;

    To convert between a :class:`DocumentArrayMemmap` and a :class:`DocumentArray`

    .. highlight:: python
    .. code-block:: python

        # convert from DocumentArrayMemmap to DocumentArray
        dam = DocumentArrayMemmap('./tmp')
        ...

        da = DocumentArray(dam)

        # convert from DocumentArray to DocumentArrayMemmap
        dam2 = DocumentArrayMemmap('./tmp')
        dam2.extend(da)
    """

    def __init__(self, path: str, key_length: int = 36):
        Path(path).mkdir(parents=True, exist_ok=True)
        self._header_path = os.path.join(path, 'header.bin')
        self._body_path = os.path.join(path, 'body.bin')
        self._key_length = key_length
        self._load_header_body()

    def reload(self):
        """Reload header of this object from the disk.

        This function is useful when another thread/process modify the on-disk storage and
        the change has not been reflected in this :class:`DocumentArray` object.

        This function only reloads the header, not the body.
        """
        self._load_header_body()

    def _load_header_body(self, mode: str = 'a'):
        if hasattr(self, '_header'):
            self._header.close()
        if hasattr(self, '_body'):
            self._body.close()

        open(self._header_path, mode).close()
        open(self._body_path, mode).close()

        self._header = open(self._header_path, 'r+b')
        self._body = open(self._body_path, 'r+b')

        tmp = np.frombuffer(
            self._header.read(),
            dtype=[
                ('', (np.str_, self._key_length)),  # key_length x 4 bytes
                ('', np.int64),  # 8 bytes
                ('', np.int64),  # 8 bytes
                ('', np.int64),  # 8 bytes
            ],
        )
        self._header_entry_size = 24 + 4 * self._key_length

        self._header_map = {
            r[0]: (idx, r[1], r[2], r[3])
            for idx, r in enumerate(tmp)
            if not np.array_equal((r[1], r[2], r[3]), HEADER_NONE_ENTRY)
        }
        self._body_fileno = self._body.fileno()
        self._start = 0
        if self._header_map:
            self._start = tmp[-1][1] + tmp[-1][3]
            self._body.seek(self._start)

    def __len__(self):
        return len(self._header_map)

    def extend(self, values: Iterable['Document']) -> None:
        """Extend the :class:`DocumentArrayMemmap` by appending all the items from the iterable.

        :param values: the iterable of Documents to extend this array with
        """
        for d in values:
            self.append(d, flush=False)
        self._header.flush()
        self._body.flush()

    def clear(self) -> None:
        """Clear the on-disk data of :class:`DocumentArrayMemmap`"""
        self._load_header_body('wb')

    def append(self, doc: 'Document', flush: bool = True) -> None:
        """
        Append :param:`doc` in :class:`DocumentArrayMemmap`.

        :param doc: The doc needs to be appended.
        :param flush: If set, then flush to disk on done.
        """
        value = doc.binary_str()
        l = len(value)  #: the length
        p = int(self._start / PAGE_SIZE) * PAGE_SIZE  #: offset of the page
        r = (
            self._start % PAGE_SIZE
        )  #: the remainder, i.e. the start position given the offset
        self._header.write(
            np.array(
                (doc.id, p, r, r + l),
                dtype=[
                    ('', (np.str_, self._key_length)),
                    ('', np.int64),
                    ('', np.int64),
                    ('', np.int64),
                ],
            ).tobytes()
        )
        self._header_map[doc.id] = (len(self._header_map), p, r, r + l)
        self._start = p + r + l
        self._body.write(value)
        if flush:
            self._header.flush()
            self._body.flush()

    def __getitem__(self, key: Union[int, str]) -> 'Document':
        if isinstance(key, str):
            pos_info = self._header_map[key]
            _, p, r, l = pos_info
            with mmap.mmap(self._body_fileno, offset=p, length=l) as m:
                return Document(m[r:])
        elif isinstance(key, int):
            return self[self._int2str_id(key)]
        else:
            raise TypeError(f'`key` must be int or str, but receiving {key!r}')

    def __delitem__(self, key: Union[int, str]):
        if isinstance(key, str):
            idx = self._str2int_id(key)
            str_key = key
        elif isinstance(key, int):
            idx = key
            str_key = self._int2str_id(idx)
        else:
            raise TypeError(f'`key` must be int or str, but receiving {key!r}')

        p = idx * self._header_entry_size
        self._header.seek(p, 0)
        self._header.write(
            np.array(
                (key, -1, -1, -1),
                dtype=[
                    ('', (np.str_, self._key_length)),
                    ('', np.int64),
                    ('', np.int64),
                    ('', np.int64),
                ],
            ).tobytes()
        )
        self._header.seek(0, 2)
        self._header.flush()
        self._header_map.pop(str_key)

    def _str2int_id(self, key: str) -> int:
        return self._header_map[key][0]

    def _int2str_id(self, key: int) -> str:
        p = key * self._header_entry_size
        self._header.seek(p, 0)
        d_id = np.frombuffer(
            self._header.read(4 * self._key_length), dtype=(np.str_, self._key_length)
        )
        self._header.seek(0, 2)
        return d_id[0]

    def __iter__(self) -> Iterator['Document']:
        for k in self._header_map.keys():
            yield self[k]

    def __setitem__(self, key: Union[int, str], value: 'Document') -> None:
        if isinstance(key, int):
            if 0 <= key < len(self):
                # override an existing entry
                self.append(value)
                self._header_map[self._int2str_id(key)] = self._header_map[value.id]
                del self[value.id]
            else:
                raise IndexError(f'`key`={key} is out of range')
        elif isinstance(key, str):
            value.id = key
            self.append(value)
        else:
            raise TypeError(f'`key` must be int or str, but receiving {key!r}')

    @classmethod
    def _flatten(cls, sequence):
        return itertools.chain.from_iterable(sequence)

    def __bool__(self):
        """To simulate ```l = []; if l: ...```

        :return: returns true if the length of the array is larger than 0
        """
        return len(self) > 0

    def __eq__(self, other):
        return (
            type(self) is type(other)
            and self._header_path == other._header_path
            and self._body_path == other._body_path
        )

    def __contains__(self, item: str):
        return item in self._header_map

    def prune(self) -> None:
        """Prune deleted Documents from this object, this yields a smaller on-disk storage. """
        tdir = tempfile.mkdtemp()
        dam = DocumentArrayMemmap(tdir, key_length=self._key_length)
        dam.extend(self)
        dam.reload()
        os.remove(self._body_path)
        os.remove(self._header_path)
        shutil.copy(os.path.join(tdir, 'header.bin'), self._header_path)
        shutil.copy(os.path.join(tdir, 'body.bin'), self._body_path)
        self.reload()

    @property
    def physical_size(self) -> int:
        """Return the on-disk physical size of this DocumentArrayMemmap, in bytes

        :return: the number of bytes
        """
        return os.stat(self._header_path).st_size + os.stat(self._body_path).st_size
