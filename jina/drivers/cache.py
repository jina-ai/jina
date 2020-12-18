from typing import Any, Dict

from .index import BaseIndexDriver
from ..executors.indexers.cache import DATA_FIELD

if False:
    from .. import Document
    from ..types.sets import DocumentSet

ID_KEY = 'id'
CONTENT_HASH_KEY = 'content_hash'


class BaseCacheDriver(BaseIndexDriver):
    """
    The driver related to :class:`BaseCache`
    """

    supported_fields = [ID_KEY, CONTENT_HASH_KEY]
    default_field = ID_KEY

    def __init__(self, with_serialization: bool = False, *args, **kwargs):
        """
        :param with_serialization: feed serialized doc to the CacheIndexer
        :param args:
        :param kwargs:
        """
        self.with_serialization = with_serialization
        super().__init__(*args, **kwargs)
        self.field = kwargs.get('field', self.default_field)
        if self.field not in self.supported_fields:
            raise ValueError(f"Field '{self.field}' not in supported list of {self.supported_fields}")

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        for d in docs:
            if self.field == ID_KEY:
                result = self.exec[d.id]
            elif self.field == CONTENT_HASH_KEY:
                result = self.exec[d.content_hash]
            if result is None:
                self.on_miss(d)
            else:
                self.on_hit(d, result)

    def on_miss(self, doc: 'Document') -> None:
        """Function to call when doc is missing, the default behavior is add to cache when miss
        :param doc: the document in the request but missed in the cache
        """
        data = doc.id
        if self.field == CONTENT_HASH_KEY:
            data = doc.content_hash

        if self.with_serialization:
            self.exec_fn(doc.id, doc.SerializeToString(), **{DATA_FIELD: data})
        else:
            self.exec_fn(doc.id, **{DATA_FIELD: data})

    def on_hit(self, req_doc: 'Document', hit_result: Any) -> None:
        """ Function to call when doc is hit
        :param req_doc: the document in the request and hitted in the cache
        :param hit_result: the hit result returned by the cache
        :return:
        """
        pass


class TaggingCacheDriver(BaseCacheDriver):
    """Label the hit-cache docs with certain tags """

    def __init__(self, tags: Dict, *args, **kwargs):
        """
        :param tags: the tags to be updated on hit docs
        """
        super().__init__(*args, **kwargs)
        self._tags = tags

    def on_hit(self, req_doc: 'Document', hit_result: Any) -> None:
        req_doc.tags.update(self._tags)
