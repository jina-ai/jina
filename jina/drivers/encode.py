__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional

from . import BaseExecutableDriver, FlatRecursiveMixin
from ..types.sets import DocumentSet
from ..excepts import LengthMismatchException


class BaseEncodeDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`encode` by default """

    def __init__(
        self, executor: Optional[str] = None, method: str = 'encode', *args, **kwargs
    ):
        super().__init__(executor, method, *args, **kwargs)


class EncodeDriver(FlatRecursiveMixin, BaseEncodeDriver):
    """Extract the content from documents and call executor and do encoding"""

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        contents, docs_pts = docs.all_contents

        if docs_pts:
            embeds = self.exec_fn(contents)
            if len(docs_pts) != embeds.shape[0]:
                msg = (
                    f'mismatched {len(docs_pts)} docs from level {docs_pts[0].granularity} '
                    f'and a {embeds.shape} shape embedding, the first dimension must be the same'
                )
                self.logger.error(msg)
                raise LengthMismatchException(msg)
            for doc, embedding in zip(docs_pts, embeds):
                doc.embedding = embedding


class ScipySparseEncodeDriver(FlatRecursiveMixin, BaseEncodeDriver):
    """Extract the content from documents and call executor and do encoding"""

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        contents, docs_pts = docs.all_contents

        if docs_pts:
            embeds = self.exec_fn(contents)
            if len(docs_pts) != embeds.shape[0]:
                msg = (
                    f'mismatched {len(docs_pts)} docs from level {docs_pts[0].granularity} '
                    f'and a {embeds.shape} shape embedding, the first dimension must be the same'
                )
                self.logger.error(msg)
                raise LengthMismatchException(msg)
            for idx, doc in enumerate(docs_pts):
                doc.embedding = embeds.getrow(idx)
