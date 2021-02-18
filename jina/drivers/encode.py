__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import warnings
from typing import Optional

from . import BaseExecutableDriver, FastRecursiveMixin, RecursiveMixin
from ..types.sets import DocumentSet


class BaseEncodeDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`encode` by default """

    def __init__(self,
                 executor: str = None,
                 method: str = 'encode',
                 *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class EncodeDriver(FastRecursiveMixin, BaseEncodeDriver):
    """Extract the content from documents and call executor and do encoding
    """

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        contents, docs_pts = docs.all_contents

        if docs_pts:
            embeds = self.exec_fn(contents)
            if len(docs_pts) != embeds.shape[0]:
                self.logger.error(
                    f'mismatched {len(docs_pts)} docs from level {docs_pts[0].granularity} '
                    f'and a {embeds.shape} shape embedding, the first dimension must be the same')
            for doc, embedding in zip(docs_pts, embeds):
                doc.embedding = embedding


class LegacyEncodeDriver(RecursiveMixin, BaseEncodeDriver):
    """Extract the content from documents and call executor and do encoding

    .. note::

        ``batch_size`` is specially useful when the same EncoderExecutor can be used for documents of different granularities
         (chunks, chunks of chunks ...)

    .. warning::

        ``batch_size`` parameter was added to cover the case where root documents had very few chunks, and the encoder executor could
        then only process them in batches of the chunk size of each document, which did not lead to the full use of batching capabilities
        of the powerful Executors

    :param batch_size: number of documents to be used simultaneously in the encoder :meth:_apply_all.
    :param *args: *args for super
    :param **kwargs: **kwargs for super
    """

    class CacheDocumentSet:
        """Helper class to accumulate documents from different DocumentSets in a single DocumentSet
         to help guarantee that the encoder driver can consume documents in fixed batch sizes to allow
         the EncoderExecutors to leverage its batching abilities.
         It is useful to have batching even when chunks are involved"""

        def __init__(self,
                     capacity: Optional[int] = None,
                     *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.capacity = capacity
            self._doc_set = DocumentSet(docs_proto=[])

        @property
        def available_capacity(self):
            """The capacity left in the cache


            .. # noqa: DAR201
            """
            return self.capacity - len(self._doc_set)

        def cache(self, docs: DocumentSet):
            """Cache the docs in DocumentSet.

            :param docs: the DocumentSet to cache
            :return: the subset of the docs
            """
            docs_to_append = min(len(docs), self.available_capacity)
            self._doc_set.extend(docs[: docs_to_append])
            return DocumentSet(docs[docs_to_append:])

        def __len__(self):
            return len(self._doc_set)

        def get(self):
            """Get the DocumentSet


            .. # noqa: DAR201
            """
            return self._doc_set

    def __init__(self,
                 batch_size: Optional[int] = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        warnings.warn(f'this drivers will be removed soon, use {EncodeDriver!r} instead', DeprecationWarning)
        self.batch_size = batch_size
        if self.batch_size:
            self.cache_set = LegacyEncodeDriver.CacheDocumentSet(capacity=self.batch_size)
        else:
            self.cache_set = None

    def __call__(self, *args, **kwargs):
        """Traverse the documents with the Driver.

        :param *args: *args for ``_traverse_apply``
        :param **kwargs: **kwargs for ``_traverse_apply``
        """
        self._traverse_apply(self.docs, *args, **kwargs)
        self._empty_cache()

    def _apply_batch(self, batch: 'DocumentSet'):
        contents, docs_pts = batch.all_contents

        if docs_pts:
            embeds = self.exec_fn(contents)
            if embeds is None:
                self.logger.error(
                    f'{self.exec_fn!r} returns nothing, you may want to check the implementation of {self.exec!r}')
            elif len(docs_pts) != embeds.shape[0]:
                self.logger.error(
                    f'mismatched {len(docs_pts)} docs from level {docs_pts[0].granularity} '
                    f'and a {embeds.shape} shape embedding, the first dimension must be the same')
            else:
                for doc, embedding in zip(docs_pts, embeds):
                    doc.embedding = embedding

    def _empty_cache(self):
        if self.batch_size:
            cached_docs = self.cache_set.get()
            if len(cached_docs) > 0:
                self._apply_batch(cached_docs)
            self.cache_set = LegacyEncodeDriver.CacheDocumentSet(capacity=self.batch_size)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        if self.cache_set is not None:
            left_docs = self.cache_set.cache(docs)
            while len(left_docs) > 0:
                self._empty_cache()
                left_docs = self.cache_set.cache(left_docs)
            if self.cache_set.available_capacity == 0:
                self._empty_cache()
        else:
            self._apply_batch(docs)
