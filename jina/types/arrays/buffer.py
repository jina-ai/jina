from jina.types.arrays import DocumentArray
from ... import Document

if False:
    from .memmap import DocumentArrayMemmap


class BufferPoolManager:
    """
    Create a buffer pool manager that maps hot :class:`Document` s of a :class:`DocumentArrayMemmap` to a memory buffer.

    This helps keep access to memory-loaded :class:`Document` instances synced with :class:`DocumentArrayMemmap` values.
    The memory buffer has a fixed size and uses an LRU strategy to empty spots when full.
    """

    def __init__(self, dam: 'DocumentArrayMemmap', pool_size: int = 10):
        self.pool_size = pool_size
        self.doc_map = {}  # dam_idx: (buffer_idx, content_hash)
        self.dam = dam
        self.buffer = DocumentArray()
        self._empty = []

    def _reverse_idx(self, idx):
        _idx = None
        for k, v in self.doc_map.items():
            if v[0] == idx:
                _idx = k
                break
        return idx

    def doc_is_dirty(self, idx) -> bool:
        """
        returns whether a document was changed or not.

        :param idx: id of the document
        :return: returns true if the document was changed, false otherwise
        """
        # TODO: use reverse map later
        _idx = self._reverse_idx(idx)
        return self.buffer[idx].content_hash != self.doc_map[_idx][1]

    def add_or_update(self, doc: Document):
        """
        Adds a document to the buffer pool or updates it if it already exists

        :param doc: document
        """
        # TODO: wrong, insert the document itself, otherwise, will insert a copy
        idx = doc.id
        # if document is already in buffer, update it
        if idx in self.doc_map:
            self.buffer[self.doc_map[idx][0]] = doc
        # else, if len is less than the size, append to buffer
        elif len(self.buffer) < self.pool_size:
            self.doc_map[idx] = (len(self.buffer), doc.content_hash)
            self.buffer.append(doc)
        # else, if buffer has empty spots, allocate them
        elif self._empty:
            empty_idx = self._empty.pop()
            self.doc_map[idx] = (empty_idx, doc.content_hash)
            self.buffer[empty_idx] = doc
        # else, choose a spot to free and use it
        else:
            idx_to_free = self._lru_idx()

            # if document is dirty, persist to disk
            if self.doc_is_dirty(idx_to_free):
                _idx = self._reverse_idx(idx_to_free)
                self.dam.append(self.buffer[idx_to_free])
            self.doc_map[idx] = (idx_to_free, doc.content_hash)
            self.buffer[idx_to_free] = doc

    def _lru_idx(self):
        return 0

    def __getitem__(self, key):
        return self.buffer[self.doc_map[key][0]]

    def __contains__(self, key):
        return key in self.doc_map
