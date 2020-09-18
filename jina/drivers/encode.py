__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

from . import BaseExecutableDriver
from .helper import extract_docs, array2pb

if False:
    from ..proto import jina_pb2


class BaseEncodeDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'encode', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class EncodeDriver(BaseEncodeDriver):
    """Extract the chunk-level content from documents and call executor and do encoding
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_apply = False

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        contents, docs_pts, bad_doc_ids = extract_docs(docs, embedding=False)

        if bad_doc_ids:
            self.logger.warning(f'these bad docs can not be added: {bad_doc_ids} '
                                f'from level depth {docs[0].granularity}')

        if docs_pts:
            embeds = self.exec_fn(contents)
            if len(docs_pts) != embeds.shape[0]:
                self.logger.error(
                    f'mismatched {len(docs_pts)} docs from level {docs[0].granularity} '
                    f'and a {embeds.shape} shape embedding, the first dimension must be the same')
            for doc, embedding in zip(docs_pts, embeds):
                doc.embedding.CopyFrom(array2pb(embedding))
