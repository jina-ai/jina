import itertools
import mmap
import os
import shutil
import tempfile
import warnings
from collections import OrderedDict
from collections.abc import MutableSequence
from pathlib import Path
from typing import Union, Iterable, Iterator, Optional, TYPE_CHECKING, List

import numpy as np

from .bpm import BufferPoolManager
from ..array.mixins import AllMixins
from ..helper import __windows__

_HEADER_NONE_ENTRY = (-1, -1, -1)
_PAGE_SIZE = mmap.ALLOCATIONGRANULARITY

if TYPE_CHECKING:
    from .. import Document, DocumentArray


class DocumentArrayMemmap(
    AllMixins,
    MutableSequence,
):
    """
    Create a memory-map to an :class:`DocumentArray` stored in binary files on disk.

    Memory-mapped files are used for accessing :class:`Document` of large :class:`DocumentArray` on disk,
    without reading the entire file into memory.

    The :class:`DocumentArrayMemmap` on-disk storage consists of two files:
        - `header.bin`: stores id, offset, length and boundary info of each Document in `body.bin`;
        - `body.bin`: stores Documents continuously

    When loading :class:`DocumentArrayMemmap`, it loads the content of `header.bin` into memory, while storing
    all `body.bin` data on disk. As `header.bin` is often much smaller than `body.bin`, memory is saved.

    :class:`DocumentArrayMemmap` also loads a portion of the documents in a memory buffer and keeps the memory documents
    synced with the disk. This helps ensure that modified documents are persisted to the disk.
    The memory buffer size is configured with parameter `buffer_pool_size` which represents the number of documents
    that the buffer can store.

    .. note::
            To make sure the documents you modify are persisted to disk, make sure that the number of referenced
            documents does not exceed the buffer pool size. Otherwise, they won't be referenced by the buffer pool and
            they will not be persisted.
            The best practice is to always reference documents using DAM.

    This class is designed to work similarly as :class:`DocumentArray` but differs in the following aspects:
        - you can set the attribute of elements in a :class:`DocumentArrayMemmap` but you need to make sure that you
        don't reference more documents than the buffer pool size
        - each document

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

    def __init__(
        self,
        path: Optional[str] = None,
        key_length: int = 36,
        buffer_pool_size: int = 1000,
    ):
        if path:
            Path(path).mkdir(parents=True, exist_ok=True)
        else:
            path = tempfile.mkdtemp()
        self._path = path
        self._header_path = os.path.join(path, 'header.bin')
        self._body_path = os.path.join(path, 'body.bin')
        self._key_length = key_length
        self._last_mmap = None
        self._load_header_body()
        self._buffer_pool = BufferPoolManager(pool_size=buffer_pool_size)

    def insert(self, index: int, doc: 'Document') -> None:
        """Insert `doc` at `index`.

        :param index: the offset index of the insertion.
        :param doc: the doc needs to be inserted.
        """
        # This however must be here as inheriting from MutableSequence requires this method
        # TODO(team): implement this function if necessary and have time.
        raise NotImplementedError

    def reload(self):
        """Reload header of this object from the disk.

        This function is useful when another thread/process modify the on-disk storage and
        the change has not been reflected in this :class:`DocumentArray` object.

        This function only reloads the header, not the body.
        """
        self._load_header_body()
        self._buffer_pool.clear()

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
        self._last_header_entry = len(tmp)

        self._header_map = OrderedDict()
        for idx, r in enumerate(tmp):
            if not np.array_equal((r[1], r[2], r[3]), _HEADER_NONE_ENTRY):
                self._header_map[r[0]] = (idx, r[1], r[2], r[3])

        self._header_keys = list(self._header_map.keys())

        self._body_fileno = self._body.fileno()
        self._start = 0
        if self._header_map:
            self._start = tmp[-1][1] + tmp[-1][3]
            self._body.seek(self._start)
        self._last_mmap = None

    def __len__(self):
        return len(self._header_map)

    def extend(self, docs: Iterable['Document']) -> None:
        """Extend the :class:`DocumentArrayMemmap` by appending all the items from the iterable.

        :param docs: the iterable of Documents to extend this array with
        """
        if not docs:
            return

        for d in docs:
            self.append(d, flush=False)
        self._header.flush()
        self._body.flush()
        self._last_mmap = None

    def clear(self) -> None:
        """Clear the on-disk data of :class:`DocumentArrayMemmap`"""
        self._load_header_body('wb')

    def _update_or_append(
        self,
        doc: 'Document',
        idx: Optional[int] = None,
        flush: bool = True,
        update_buffer: bool = True,
    ) -> None:
        value = bytes(doc)
        l = len(value)  #: the length
        p = int(self._start / _PAGE_SIZE) * _PAGE_SIZE  #: offset of the page
        r = (
            self._start % _PAGE_SIZE
        )  #: the remainder, i.e. the start position given the offset

        if idx is not None:
            self._header.seek(idx * self._header_entry_size, 0)

        if (doc.id is not None) and len(doc.id) > self._key_length:
            warnings.warn(
                f'The ID of doc ({doc.id}) will be truncated to the maximum length {self._key_length}'
            )

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
        if idx is None:
            self._header_map[doc.id] = (self._last_header_entry, p, r, r + l)
            self._last_header_entry = self._last_header_entry + 1
            self._header_keys.append(doc.id)
        else:
            self._header_map[doc.id] = (idx, p, r, r + l)
            self._header_keys[idx] = doc.id
            self._header.seek(0, 2)
        self._start = p + r + l
        self._body.write(value)
        if flush:
            self._header.flush()
            self._body.flush()
            self._last_mmap = None
        if update_buffer:
            result = self._buffer_pool.add_or_update(doc.id, doc)
            if result:
                _key, _doc = result
                self._update(_doc, self._str2int_id(_key), update_buffer=False)

    def append(
        self, doc: 'Document', flush: bool = True, update_buffer: bool = True
    ) -> None:
        """
        Append `doc` in :class:`DocumentArrayMemmap`.

        :param doc: The doc needs to be appended.
        :param update_buffer: If set, update the buffer.
        :param flush: If set, then flush to disk on done.
        """
        self._update_or_append(doc, flush=flush, update_buffer=update_buffer)

    def _update(
        self, doc: 'Document', idx: int, flush: bool = True, update_buffer: bool = True
    ) -> None:
        """
        Update `doc` in :class:`DocumentArrayMemmap`.

        :param doc: The doc needed to be updated.
        :param idx: The position of the document.
        :param update_buffer: If set, update the buffer.
        :param flush: If set, then flush to disk on done.
        """
        self._update_or_append(doc, idx=idx, flush=flush, update_buffer=update_buffer)

    def _iteridx_by_slice(self, s: slice):
        length = self.__len__()
        start, stop, step = (
            s.start or 0,
            s.stop if s.stop is not None else length,
            s.step or 1,
        )
        if 0 > stop >= -length:
            stop = stop + length

        if 0 > start >= -length:
            start = start + length

        # if start and stop are in order, put them inside bounds
        # otherwise, range will return an empty iterator
        if start <= stop:
            if (start < 0 and stop < 0) or (start > length and stop > length):
                start, stop = 0, 0
            elif start < 0 and stop > length:
                start, stop = 0, length
            elif start < 0:
                start = 0
            elif stop > length:
                stop = length

        return range(start, stop, step)

    def _get_doc_array_by_slice(self, s: slice):
        from .. import DocumentArray

        da = DocumentArray()
        for i in self._iteridx_by_slice(s):
            da.append(self[self._int2str_id(i)])

        return da

    @property
    def _mmap(self) -> 'mmap':
        if self._last_mmap is None:
            self._last_mmap = (
                mmap.mmap(self._body_fileno, length=0)
                if __windows__
                else mmap.mmap(self._body_fileno, length=0, prot=mmap.PROT_READ)
            )
        if __windows__:
            self._body.seek(self._start)
        return self._last_mmap

    def _get_doc_by_key(self, key: str):
        """
        returns a document by key (ID) from disk

        :param key: id of the document
        :return: returns a document
        """
        pos_info = self._header_map[key]
        _, p, r, r_plus_l = pos_info
        from .. import Document

        return Document(self._mmap[p + r : p + r_plus_l])

    def __getitem__(self, key: Union[int, str, slice, List]):
        if isinstance(key, str):
            if key in self._buffer_pool:
                return self._buffer_pool[key]
            doc = self._get_doc_by_key(key)
            result = self._buffer_pool.add_or_update(key, doc)
            if result:
                _key, _doc = result
                self._update(_doc, self._str2int_id(_key), update_buffer=False)
            return doc

        elif isinstance(key, int):
            return self[self._int2str_id(key)]
        elif isinstance(key, slice):
            return self._get_doc_array_by_slice(key)
        elif isinstance(key, list):
            from .. import DocumentArray

            return DocumentArray(self[k] for k in key)
        else:
            raise TypeError(f'`key` must be int, str or slice, but receiving {key!r}')

    def _del_doc(self, idx: int, str_key: str):
        p = idx * self._header_entry_size
        self._header.seek(p, 0)

        self._header.write(
            np.array(
                (str_key, -1, -1, -1),
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
        self._last_mmap = None
        pop_idx = self._header_keys.index(str_key)
        self._header_map.pop(str_key)
        self._header_keys.pop(pop_idx)
        self._buffer_pool.delete_if_exists(str_key)

    def __delitem__(self, key: Union[int, str, slice]):
        if isinstance(key, str):
            idx = self._str2int_id(key)
            str_key = key
            self._del_doc(idx, str_key)
        elif isinstance(key, int):
            idx = key
            str_key = self._int2str_id(idx)
            self._del_doc(idx, str_key)
        elif isinstance(key, slice):
            for idx in reversed(self._iteridx_by_slice(key)):
                str_key = self._int2str_id(idx)
                self._del_doc(idx, str_key)
        else:
            raise TypeError(f'`key` must be int, str or slice, but receiving {key!r}')

    def _str2int_id(self, key: str) -> int:
        return self._header_map[key][0]

    def _int2str_id(self, key: int) -> str:
        # i < 0 needs to be handled
        return self._header_keys[key]

    def __iter__(self) -> Iterator['Document']:
        for k in self._header_map.keys():
            yield self[k]

    def __setitem__(self, key: Union[int, str], value: 'Document') -> None:
        if isinstance(key, int):
            if 0 <= key < len(self):
                str_key = self._int2str_id(key)
                # override an existing entry
                self._update(value, key)

                # allows overwriting an existing document
                if str_key != value.id:
                    entry = self._header_map.pop(value.id)
                    self._header_map = OrderedDict(
                        [
                            (value.id, entry) if k == str_key else (k, v)
                            for k, v in self._header_map.items()
                        ]
                    )
                    if str_key in self._buffer_pool.doc_map:
                        self._buffer_pool.doc_map.pop(str_key)
            else:
                raise IndexError(f'`key`={key} is out of range')
        elif isinstance(key, str):
            if key != value.id:
                raise ValueError('key must be equal to document id')
            self._update(value, self._str2int_id(key))
        else:
            raise TypeError(f'`key` must be int or str, but receiving {key!r}')

    def __eq__(self, other):
        return (
            type(self) is type(other)
            and self._header_path == other._header_path
            and self._body_path == other._body_path
        )

    def __contains__(self, item: str):
        return item in self._header_map

    def flush(self) -> None:
        """Persists memory loaded documents to disk"""
        docs_to_flush = self._buffer_pool.docs_to_flush()
        for key, doc in docs_to_flush:
            self._update(doc, self._str2int_id(key), flush=False)
        self._header.flush()
        self._body.flush()
        self._last_mmap = None

    def __del__(self):
        try:
            self.flush()
        except:
            warnings.warn(f'{self!r} is not correctly flush to disk on deconstruction.')

    def prune(self) -> None:
        """Prune deleted Documents from this object, this yields a smaller on-disk storage. """
        dam = DocumentArrayMemmap(key_length=self._key_length)
        dam.extend(self)
        dam.reload()
        if hasattr(self, '_body'):
            self._body.close()
        os.remove(self._body_path)
        if hasattr(self, '_header'):
            self._header.close()
        os.remove(self._header_path)
        shutil.copy(os.path.join(dam.path, 'header.bin'), self._header_path)
        shutil.copy(os.path.join(dam.path, 'body.bin'), self._body_path)
        self.reload()

    @property
    def physical_size(self) -> int:
        """Return the on-disk physical size of this DocumentArrayMemmap, in bytes

        :return: the number of bytes
        """
        return os.stat(self._header_path).st_size + os.stat(self._body_path).st_size

    @staticmethod
    def _flatten(sequence):
        return itertools.chain.from_iterable(sequence)

    @property
    def path(self) -> str:
        """Get the path where the instance is stored.

        :returns: The stored path of the memmap instance.
        """
        return self._path

    @property
    def _pb_body(self):
        for v in self:
            yield v.proto
