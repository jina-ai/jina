import itertools
import mmap
import os
import shutil
import tempfile
from collections import OrderedDict
from collections.abc import Iterable as Itr
from pathlib import Path
from typing import (
    Union,
    Iterable,
    Iterator,
    List,
    Tuple,
    Optional,
)

import numpy as np

from ... import __windows__

from .abstract import AbstractDocumentArray
from .bpm import BufferPoolManager
from .document import DocumentArray, DocumentArrayGetAttrMixin
from .neural_ops import DocumentArrayNeuralOpsMixin
from .search_ops import DocumentArraySearchOpsMixin
from .traversable import TraversableSequence
from ..document import Document
from ..struct import StructView
from ...logging.predefined import default_logger


HEADER_NONE_ENTRY = (-1, -1, -1)
PAGE_SIZE = mmap.ALLOCATIONGRANULARITY


class DocumentArrayMemmap(
    TraversableSequence,
    DocumentArrayGetAttrMixin,
    DocumentArrayNeuralOpsMixin,
    DocumentArraySearchOpsMixin,
    Itr,
    AbstractDocumentArray,
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

    def __init__(self, path: str, key_length: int = 36, buffer_pool_size: int = 1000):
        Path(path).mkdir(parents=True, exist_ok=True)
        self._path = path
        self._header_path = os.path.join(path, 'header.bin')
        self._body_path = os.path.join(path, 'body.bin')
        self._embeddings_path = os.path.join(path, 'embeddings.bin')
        self._key_length = key_length
        self._last_mmap = None
        self._load_header_body()
        self._embeddings_shape = None
        self.buffer_pool = BufferPoolManager(pool_size=buffer_pool_size)

    def reload(self):
        """Reload header of this object from the disk.

        This function is useful when another thread/process modify the on-disk storage and
        the change has not been reflected in this :class:`DocumentArray` object.

        This function only reloads the header, not the body.
        """
        self._load_header_body()
        self.buffer_pool.clear()

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
        self.last_header_entry = len(tmp)

        self._header_map = OrderedDict()
        for idx, r in enumerate(tmp):
            if not np.array_equal((r[1], r[2], r[3]), HEADER_NONE_ENTRY):
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

    def extend(self, values: Iterable['Document']) -> None:
        """Extend the :class:`DocumentArrayMemmap` by appending all the items from the iterable.

        :param values: the iterable of Documents to extend this array with
        """
        for d in values:
            self.append(d, flush=False)
        self._header.flush()
        self._body.flush()
        self._last_mmap = None

    def clear(self) -> None:
        """Clear the on-disk data of :class:`DocumentArrayMemmap`"""
        self._load_header_body('wb')
        self._invalidate_embeddings_memmap()

    def _update_or_append(
        self,
        doc: 'Document',
        idx: Optional[int] = None,
        flush: bool = True,
        update_buffer: bool = True,
    ) -> None:
        value = doc.binary_str()
        l = len(value)  #: the length
        p = int(self._start / PAGE_SIZE) * PAGE_SIZE  #: offset of the page
        r = (
            self._start % PAGE_SIZE
        )  #: the remainder, i.e. the start position given the offset

        if idx is not None:
            self._header.seek(idx * self._header_entry_size, 0)

        if (doc.id is not None) and len(doc.id) > self._key_length:
            default_logger.warning(
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
            self._header_map[doc.id] = (self.last_header_entry, p, r, r + l)
            self.last_header_entry = self.last_header_entry + 1
            self._header_keys.append(doc.id)
        else:
            self._header_map[doc.id] = (idx, p, r, r + l)
            self._header_keys[idx] = doc.id
            self._header.seek(0, 2)
        self._start = p + r + l
        self._body.write(value)
        self._invalidate_embeddings_memmap()
        if flush:
            self._header.flush()
            self._body.flush()
            self._last_mmap = None
        if update_buffer:
            result = self.buffer_pool.add_or_update(doc.id, doc)
            if result:
                _key, _doc = result
                self._update(_doc, self._str2int_id(_key), update_buffer=False)

    def append(
        self, doc: 'Document', flush: bool = True, update_buffer: bool = True
    ) -> None:
        """
        Append :param:`doc` in :class:`DocumentArrayMemmap`.

        :param doc: The doc needs to be appended.
        :param update_buffer: If set, update the buffer.
        :param flush: If set, then flush to disk on done.
        """
        self._update_or_append(doc, flush=flush, update_buffer=update_buffer)

    def _update(
        self, doc: 'Document', idx: int, flush: bool = True, update_buffer: bool = True
    ) -> None:
        """
        Update :param:`doc` in :class:`DocumentArrayMemmap`.

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
        from .document import DocumentArray

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

    def get_doc_by_key(self, key: str):
        """
        returns a document by key (ID) from disk

        :param key: id of the document
        :return: returns a document
        """
        pos_info = self._header_map[key]
        _, p, r, r_plus_l = pos_info
        return Document(self._mmap[p + r : p + r_plus_l])

    def __getitem__(self, key: Union[int, str, slice]):
        if isinstance(key, str):
            if key in self.buffer_pool:
                return self.buffer_pool[key]
            doc = self.get_doc_by_key(key)
            result = self.buffer_pool.add_or_update(key, doc)
            if result:
                _key, _doc = result
                self._update(_doc, self._str2int_id(_key), update_buffer=False)
            return doc

        elif isinstance(key, int):
            return self[self._int2str_id(key)]
        elif isinstance(key, slice):
            return self._get_doc_array_by_slice(key)
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
        self.buffer_pool.delete_if_exists(str_key)
        self._invalidate_embeddings_memmap()

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
                    if str_key in self.buffer_pool.doc_map:
                        self.buffer_pool.doc_map.pop(str_key)
            else:
                raise IndexError(f'`key`={key} is out of range')
        elif isinstance(key, str):
            if key != value.id:
                raise ValueError('key must be equal to document id')
            self._update(value, self._str2int_id(key))
        else:
            raise TypeError(f'`key` must be int or str, but receiving {key!r}')

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

    def save(self) -> None:
        """Persists memory loaded documents to disk"""
        docs_to_flush = self.buffer_pool.docs_to_flush()
        for key, doc in docs_to_flush:
            self._update(doc, self._str2int_id(key), flush=False)
        self._header.flush()
        self._body.flush()
        self._last_mmap = None

    def __del__(self):
        self.save()

    def prune(self) -> None:
        """Prune deleted Documents from this object, this yields a smaller on-disk storage. """
        tdir = tempfile.mkdtemp()
        dam = DocumentArrayMemmap(tdir, key_length=self._key_length)
        dam.extend(self)
        dam.reload()
        if hasattr(self, '_body'):
            self._body.close()
        os.remove(self._body_path)
        if hasattr(self, '_header'):
            self._header.close()
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

    def get_attributes(self, *fields: str) -> Union[List, List[List]]:
        """Return all nonempty values of the fields from all docs this array contains

        :param fields: Variable length argument with the name of the fields to extract
        :return: Returns a list of the values for these fields.
            When `fields` has multiple values, then it returns a list of list.
        """
        index = None
        fields = list(fields)
        if 'embedding' in fields:
            embeddings = list(self.embeddings)  # type: List[np.ndarray]
            index = fields.index('embedding')
            fields.remove('embedding')
        if fields:
            contents = [doc.get_attributes(*fields) for doc in self]
            if len(fields) > 1:
                contents = list(map(list, zip(*contents)))
            if index:
                contents = [contents]
                contents.insert(index, embeddings)
            return contents
        else:
            return embeddings

    def get_attributes_with_docs(
        self,
        *fields: str,
    ) -> Tuple[Union[List, List[List]], 'DocumentArray']:
        """Return all nonempty values of the fields together with their nonempty docs

        :param fields: Variable length argument with the name of the fields to extract
        :return: Returns a tuple. The first element is  a list of the values for these fields.
            When `fields` has multiple values, then it returns a list of list. The second element is the non-empty docs.
        """

        contents = []
        docs_pts = []

        for doc in self:
            contents.append(doc.get_attributes(*fields))
            docs_pts.append(doc)

        if len(fields) > 1:
            contents = list(map(list, zip(*contents)))

        return contents, DocumentArray(docs_pts)

    @property
    def _embeddings_memmap(self) -> Optional[np.ndarray]:
        """Return the cached embedding stored in np.memmap.

        :returns: Embeddings as np.ndarray stored in memmap, if not persist, return None.
        """
        if self._embeddings_shape:
            # The memmap object can be used anywhere an ndarray is accepted.
            # Given a memmap fp, isinstance(fp, numpy.ndarray) returns True.
            return np.memmap(
                self._embeddings_path,
                mode='r',
                dtype='float',
                shape=self._embeddings_shape,
            )

    @_embeddings_memmap.setter
    def _embeddings_memmap(self, other_embeddings: Optional[np.ndarray]):
        """Set the cached embedding values in case it is not cached.

        :param other_embeddings: The embedding to be stored into numpy.memmap, or can be set
            to None to invalidate the property.
        """
        if other_embeddings is not None:
            fp = np.memmap(
                self._embeddings_path,
                dtype='float',
                mode='w+',
                shape=other_embeddings.shape,
            )
            self._embeddings_shape = other_embeddings.shape
            fp[:] = other_embeddings[:]
            fp.flush()
            del fp

    @property
    def embeddings(self) -> np.ndarray:
        """Return a `np.ndarray` stacking all the `embedding` attributes as rows.

        :return: embeddings stacked per row as `np.ndarray`.

        .. warning:: This operation assumes all embeddings have the same shape and dtype.
            All dtype and shape values are assumed to be equal to the values of the
            first element in the DocumentArray / DocumentArrayMemmap.

        .. warning:: This operation currently does not support sparse arrays.
        """
        if self._embeddings_memmap is not None:
            return self._embeddings_memmap

        x_mat = b''.join(d.proto.embedding.dense.buffer for d in self)
        embeds = np.frombuffer(
            x_mat, dtype=self[0].proto.embedding.dense.dtype
        ).reshape((len(self), self[0].proto.embedding.dense.shape[0]))

        self._embeddings_memmap = embeds

        return embeds

    @embeddings.setter
    def embeddings(self, emb: np.ndarray):
        """Set the embeddings of the Documents

        :param emb: The embedding matrix to set
        """
        if len(emb) != len(self):
            raise ValueError(
                f'the number of rows in the input ({len(emb)}), should match the'
                f'number of Documents ({len(self)})'
            )

        for d, x in zip(self, emb):
            d.embedding = x

    @DocumentArrayGetAttrMixin.tags.getter
    def tags(self) -> List[StructView]:
        """Get the tags attribute of all Documents

        :return: List of ``tags`` attributes for all Documents
        """
        return self.get_attributes('tags')

    @DocumentArrayGetAttrMixin.texts.getter
    def texts(self) -> List[str]:
        """Get the text attribute of all Documents

        :return: List of ``text`` attributes for all Documents
        """
        return self.get_attributes('text')

    @DocumentArrayGetAttrMixin.buffers.getter
    def buffers(self) -> List[bytes]:
        """Get the buffer attribute of all Documents

        :return: List of ``buffer`` attributes for all Documents
        """
        return self.get_attributes('buffer')

    @DocumentArrayGetAttrMixin.blobs.getter
    def blobs(self) -> np.ndarray:
        """Return a `np.ndarray` stacking all the `blob` attributes.

        The `blob` attributes are stacked together along a newly created first
        dimension (as if you would stack using ``np.stack(X, axis=0)``).

        .. warning:: This operation assumes all blobs have the same shape and dtype.
                 All dtype and shape values are assumed to be equal to the values of the
                 first element in the DocumentArray / DocumentArrayMemmap

        .. warning:: This operation currently does not support sparse arrays.

        :return: blobs stacked per row as `np.ndarray`.
        """

        blobs = np.stack(self.get_attributes('blob'))
        return blobs

    def _invalidate_embeddings_memmap(self):
        self._embeddings_memmap = None
        self._embeddings_shape = None

    @staticmethod
    def _flatten(sequence):
        return itertools.chain.from_iterable(sequence)

    @property
    def path(self) -> str:
        """Get the path where the instance is stored.

        :returns: The stored path of the memmap instance.
        """
        return self._path
