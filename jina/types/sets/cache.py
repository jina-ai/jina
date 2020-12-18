from typing import Optional
from .document import DocumentSet


class CacheDocumentSet:

    def __init__(self,
                 capacity: Optional[int] = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.capacity = capacity
        self._doc_set = DocumentSet()

    @property
    def left_capacity(self):
        return self.capacity - len(self._doc_set)

    def append(self, docs: DocumentSet):
        for doc in docs:
            self._doc_set.append(doc)

    def get(self):
        return self._doc_set
