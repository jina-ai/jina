"""Module for the Drivers for the Cache."""
from typing import Any, Dict

from .index import BaseIndexDriver
from ..executors.indexers.cache import CONTENT_HASH_KEY, ID_KEY

# noinspection PyUnreachableCode
if False:
    from .. import Document
    from ..types.sets import DocumentSet


class BaseCacheDriver(BaseIndexDriver):
    """A driver related to :class:`BaseCache`.

    :param with_serialization: feed serialized Document to the CacheIndexer
    :param *args: *args for super
    :param **kwargs: **kwargs for super
    """

    def __init__(self, with_serialization: bool = False, *args, **kwargs):
        self.with_serialization = with_serialization
        super().__init__(*args, **kwargs)
        self.field = None

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        self.field = self.exec.field

        if self._method_name == 'update':
            self.exec_fn([d.id for d in docs], [d.id if self.field == ID_KEY else d.content_hash for d in docs])
        else:
            for d in docs:
                data = d.id
                if self.field == CONTENT_HASH_KEY:
                    data = d.content_hash
                result = self.exec[data]
                if result:
                    self.on_hit(d, result)
                else:
                    self.on_miss(d, data)

    def on_miss(self, req_doc: 'Document', value: str) -> None:
        """Call when document is missing.

        The default behavior is to add to cache when miss.

        :param req_doc: the document in the request but missed in the cache
        :param value: the data besides the `req_doc.id` to be passed through to the executors
        """
        if self.with_serialization:
            self.exec_fn([req_doc.id], req_doc.SerializeToString(), [value])
        else:
            self.exec_fn([req_doc.id], [value])

    def on_hit(self, req_doc: 'Document', hit_result: Any) -> None:
        """Call when cache is hit for a document.

        :param req_doc: the document in the request and hitted in the cache
        :param hit_result: the hit result returned by the cache
        """
        pass


class TaggingCacheDriver(BaseCacheDriver):
    """A driver for labelling the hit-cache docs with certain tags."""

    def __init__(self, tags: Dict, *args, **kwargs):
        """Create a new TaggingCacheDriver.

        :param tags: the tags to be updated on hit docs
        :param *args: *args for super
        :param **kwargs: **kwargs for super
        """
        super().__init__(*args, **kwargs)
        self._tags = tags

    def on_hit(self, req_doc: 'Document', hit_result: Any) -> None:
        """Call when cache is hit for a document.

        :param req_doc: the document requested
        :param hit_result: the result of the hit
        """
        req_doc.tags.update(self._tags)
