__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional, Callable
from functools import wraps

from . import BaseExecutableDriver
from ..types.sets import DocumentSet


class BaseEncodeDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    class CacheDocumentSet:

        def __init__(self,
                     capacity: Optional[int] = None,
                     *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.capacity = capacity
            self._doc_set = DocumentSet()

        @property
        def available_capacity(self):
            return self.capacity - len(self._doc_set)

        def append(self, docs: DocumentSet):
            for doc in docs:
                self._doc_set.append(doc)

        def get(self):
            return self._doc_set

    @staticmethod
    def _batching_doc_set(func: Callable) -> Callable:

        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            docs = args[0]
            if self.cache_set:
                if self.cache_set.available_capacity >= len(docs):
                    self.cache_set.append(docs)
                else:
                    self._flush_cache(func)
                    self.cache_set.append(docs)
            else:
                func(self, *args, **kwargs)

        return arg_wrapper

    def __init__(self,
                 executor: str = None,
                 method: str = 'encode',
                 batch_size: Optional[int] = None,
                 *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)
        self.batch_size = batch_size
        if self.batch_size:
            self.cache_set = BaseEncodeDriver.CacheDocumentSet(capacity=self.batch_size)
        else:
            self.cache_set = None

    def __call__(self, *args, **kwargs):
        self._traverse_apply(self.docs, *args, **kwargs)
        self._flush_cache(self._apply_all, **kwargs)

    def _flush_cache(self, f: Callable, **kwargs):
        f(docs=self.cache_set.get(), **kwargs)
        self.cache_set = BaseEncodeDriver.CacheDocumentSet(capacity=self.batch_size)


class EncodeDriver(BaseEncodeDriver):
    """Extract the chunk-level content from documents and call executor and do encoding
    """

    @BaseEncodeDriver._batching_doc_set
    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        contents, docs_pts, bad_docs = docs.all_contents

        if bad_docs:
            self.logger.warning(f'these bad docs can not be added: {bad_docs} '
                                    f'from level depth {docs_pts[0].granularity}')

        if docs_pts:
            embeds = self.exec_fn(contents)
            if len(docs_pts) != embeds.shape[0]:
                self.logger.error(
                        f'mismatched {len(docs_pts)} docs from level {docs_pts[0].granularity} '
                        f'and a {embeds.shape} shape embedding, the first dimension must be the same')
            for doc, embedding in zip(docs_pts, embeds):
                doc.embedding = embedding
