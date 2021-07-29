from collections import OrderedDict

from ... import Document

if False:
    from .memmap import DocumentArrayMemmap


class BufferPoolManager:
    """
    Create a buffer pool manager that maps hot :class:`Document` s of a :class:`DocumentArrayMemmap` to a memory buffer.

    This helps keep access to memory-loaded :class:`Document` instances synced with :class:`DocumentArrayMemmap` values.
    The memory buffer has a fixed size and uses an LRU strategy to empty spots when full.
    """

    def __init__(self, dam: 'DocumentArrayMemmap', pool_size: int = 100000):
        self.pool_size = pool_size
        self.doc_map = OrderedDict()  # dam_idx: (buffer_idx, content_hash)
        self.dam = dam
        self.buffer = []
        self._empty = []

    def _reverse_idx(self, idx):
        _idx = None
        for k, v in self.doc_map.items():
            if v[0] == idx:
                _idx = k
                break
        return idx

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
            self.doc_map[idx] = (len(self.buffer), doc.content_hash)
            self.doc_map.move_to_end(idx)
            self.buffer.append(doc)
        # else, if buffer has empty spots, allocate them
        elif self._empty:
            empty_idx = self._empty.pop()
            self.doc_map[idx] = (empty_idx, doc.content_hash)
            self.buffer[empty_idx] = doc
            self.doc_map.move_to_end(idx)
        # else, choose a spot to free and use it
        else:
            dam_idx, (buffer_idx, content_hash) = self.doc_map.popitem(last=False)

            # if document is dirty, persist to disk
            if self.buffer[buffer_idx].content_hash != content_hash:
                self.dam.append(self.buffer[buffer_idx])
            self.doc_map[idx] = (buffer_idx, doc.content_hash)
            self.doc_map.move_to_end(idx)
            self.buffer[buffer_idx] = doc

    def delete_if_exists(self, key):
        """
        Adds a document to the buffer pool or updates it if it already exists

        :param key: document key
        """
        if key in self:
            del self[key]

    def __getitem__(self, key):
        doc = self.buffer[self.doc_map[key][0]]
        self.doc_map.move_to_end(key)
        return doc

    def __delitem__(self, key):
        buffer_idx = self.doc_map.pop(key)[0]
        self._empty.append(buffer_idx)

    def __contains__(self, key):
        return key in self.doc_map
