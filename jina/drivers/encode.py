__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import BaseExecutableDriver

if False:
    from ..types.sets import DocumentSet


class BaseEncodeDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'encode', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class EncodeDriver(BaseEncodeDriver):
    """Extract the chunk-level content from documents and call executor and do encoding
    """

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
