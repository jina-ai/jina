"""Module for the Drivers for the Cache."""
import hashlib
from typing import Any, Dict, List

from .index import BaseIndexDriver

# noinspection PyUnreachableCode
if False:
    from .. import Document
    from ..types.sets import DocumentSet


class BaseCacheDriver(BaseIndexDriver):
    """A driver related to :class:`BaseCache`.

    :param with_serialization: feed serialized Document to the CacheIndexer
    :param args: additional positional arguments which are just used for the parent initialization
    :param kwargs: additional key value arguments which are just used for the parent initialization
    """

    def __init__(self, with_serialization: bool = False, *args, **kwargs):
        self.with_serialization = with_serialization
        super().__init__(*args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        if self._method_name == 'update':
            values = [BaseCacheDriver.hash_doc(d, self.exec.fields) for d in docs]
            self.exec_fn([d.id for d in docs], values)
        else:
            for d in docs:
                value = BaseCacheDriver.hash_doc(d, self.exec.fields)
                result = self.exec[value]
                if result:
                    self.on_hit(d, result)
                else:
                    self.on_miss(d, value)

    def on_miss(self, req_doc: 'Document', value: bytes) -> None:
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

        :param req_doc: the document in the request and hit in the cache
        :param hit_result: the hit result returned by the cache
        """
        pass

    @staticmethod
    def hash_doc(doc: 'Document', fields: List[str]) -> bytes:
        """Calculate hash by which we cache.

        :param doc: the Document
        :param fields: the list of fields
        :return: the hash value of the fields
        """
        values = doc.get_attrs(*fields).values()
        data = ''
        for field, value in zip(fields, values):
            data += f'{field}:{value};'
        digest = hashlib.sha256(bytes(data.encode('utf8'))).digest()
        return digest


class TaggingCacheDriver(BaseCacheDriver):
    """A driver for labelling the hit-cache docs with certain tags."""

    def __init__(self, tags: Dict, *args, **kwargs):
        """Create a new TaggingCacheDriver.

        :param tags: the tags to be updated on hit docs
        :param args: additional positional arguments which are just used for the parent initialization
        :param kwargs: additional key value arguments which are just used for the parent initialization
        """
        super().__init__(*args, **kwargs)
        self._tags = tags

    def on_hit(self, req_doc: 'Document', hit_result: Any) -> None:
        """Call when cache is hit for a document.

        :param req_doc: the document requested
        :param hit_result: the result of the hit
        """
        req_doc.tags.update(self._tags)
