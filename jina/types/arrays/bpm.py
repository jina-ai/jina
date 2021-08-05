from collections import OrderedDict
from typing import Union

from ... import Document

if False:
    from .memmap import DocumentArrayMemmap


class BufferPoolManager:
    """
    Create a buffer pool manager that maps hot :class:`Document` s of a :class:`DocumentArrayMemmap` to a memory buffer.

    This helps keep access to memory-loaded :class:`Document` instances synced with :class:`DocumentArrayMemmap` values.
    The memory buffer has a fixed size and uses an LRU strategy to empty spots when full.
    """

    def __init__(self, dam: 'DocumentArrayMemmap', pool_size: int = 1000):
        self.pool_size = pool_size
        self.doc_map = OrderedDict()  # dam_idx: (buffer_idx, version)
        self.dam = dam
        self.buffer = []
        self._empty = []

    def add_or_update(self, idx: str, doc: Document):
        """
        Adds a document to the buffer pool or updates it if it already exists

        :param idx: index
        :param doc: document
        """
        # if document is already in buffer, update it
        if idx in self.doc_map:
            self.buffer[self.doc_map[idx][0]] = doc
            self.doc_map.move_to_end(idx)
        # else, if len is less than the size, append to buffer
        elif len(self.buffer) < self.pool_size:
            self.doc_map[idx] = (len(self.buffer), doc.version)
            self.doc_map.move_to_end(idx)
            self.buffer.append(doc)
        # else, if buffer has empty spots, allocate them
        elif self._empty:
            empty_idx = self._empty.pop()
            self.doc_map[idx] = (empty_idx, doc.version)
            self.buffer[empty_idx] = doc
            self.doc_map.move_to_end(idx)
        # else, choose a spot to free and use it with LRU strategy
        else:
            # the least recently used item is the first item in doc_map
            dam_idx, (buffer_idx, version) = self.doc_map.popitem(last=False)
            if version != self.buffer[buffer_idx].version:
                # persist to disk
                self.dam.update(
                    self.buffer[buffer_idx],
                    self.dam._str2int_id(dam_idx),
                    update_buffer=False,
                )
            self.doc_map[idx] = (buffer_idx, doc.version)
            self.doc_map.move_to_end(idx)
            self.buffer[buffer_idx] = doc

    def delete_if_exists(self, key):
        """
        Adds a document to the buffer pool or updates it if it already exists

        :param key: document key
        """
        if key in self:
            del self[key]

    def flush(self):
        """
        Persists the updated documents in disk
        """
        for _, (buffer_idx, _) in self.doc_map.items():
            self.dam.append(self.buffer[buffer_idx], update_buffer=False)

    def clear(self):
        """
        Clears the memory buffer
        """
        self.doc_map.clear()
        self.buffer = []

    def __getitem__(self, key: Union[str, int]):
        if isinstance(key, str):
            doc = self.buffer[self.doc_map[key][0]]
            self.doc_map.move_to_end(key)
            return doc
        else:
            raise TypeError(f'`key` must be str, but receiving {key!r}')

    def __delitem__(self, key):
        buffer_idx = self.doc_map.pop(key)[0]
        self._empty.append(buffer_idx)

    def __contains__(self, key):
        return key in self.doc_map
