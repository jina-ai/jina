__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional, Tuple

from . import BaseExecutableDriver, FlatRecursiveMixin
from ..excepts import LengthMismatchException
from ..types.document import Document

if False:
    from .. import DocumentSet


class SegmentDriver(FlatRecursiveMixin, BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`segment` by default """

    def __init__(
        self,
        executor: Optional[str] = None,
        method: str = 'segment',
        traversal_paths: Tuple[str] = ('r',),
        *args,
        **kwargs,
    ):
        super().__init__(
            executor, method, traversal_paths=traversal_paths, *args, **kwargs
        )

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs):
        if not docs:
            self.logger.warning(f'an empty DocumentSet {docs}')
            return

        contents, docs_pts = docs.extract_docs(*self.exec.required_keys)

        if not docs_pts:
            self.logger.warning(f'no Document is extracted {docs}')
            return

        if len(self.exec.required_keys) > 1:
            docs_chunks = self.exec_fn(*contents)
        else:
            docs_chunks = self.exec_fn(contents)

        if len(docs_pts) != len(docs_chunks):
            msg = (
                f'mismatched {len(docs_pts)} docs from level {docs_pts[0].granularity} '
                f'and length of returned crafted documents: {len(docs_chunks)}, the length must be the same'
            )
            raise LengthMismatchException(msg)

        for doc, chunks in zip(docs_pts, docs_chunks):
            self._add_chunks(doc, chunks)

    @staticmethod
    def _add_chunks(doc, chunks):
        new_chunks = []
        for chunk in chunks:
            with Document(**chunk) as c:
                if not c.mime_type:
                    c.mime_type = doc.mime_type
            new_chunks.append(c)
        doc.chunks.extend(new_chunks)
