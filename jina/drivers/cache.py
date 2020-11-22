from typing import Any, Dict

from .index import BaseIndexDriver

if False:
    from .. import Document
    from ..types.sets import DocumentSet


class BaseCacheDriver(BaseIndexDriver):
    """
    The driver related to :class:`BaseCache`

    """

    def __init__(self, with_serialization: bool = False, *args, **kwargs):
        """

        :param with_serialization: feed serialized doc to the CacheIndexer
        :param args:
        :param kwargs:
        """
        self.with_serialization = with_serialization
        super().__init__(*args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        for d in docs:
            result = self.exec[d.id]
            if result is None:
                self.on_miss(d)
            else:
                self.on_hit(d, result)

    def on_miss(self, doc: 'Document') -> None:
        """Function to call when doc is missing, the default behavior is add to cache when miss

        :param doc: the document in the request but missed in the cache
        """
        if self.with_serialization:
            self.exec_fn(doc.id, doc.SerializeToString())
        else:
            self.exec_fn(doc.id)

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
