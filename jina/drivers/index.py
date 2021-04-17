__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable, Optional

import numpy as np

from . import BaseExecutableDriver, FlatRecursiveMixin

if False:
    from ..types.sets import DocumentSet


class BaseIndexDriver(FlatRecursiveMixin, BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`add` by default """

    def __init__(
        self, executor: Optional[str] = None, method: str = 'add', *args, **kwargs
    ):
        super().__init__(executor, method, *args, **kwargs)

    def check_key_length(self, val: Iterable[str]):
        """
        Check if the max length of val(e.g. doc id) is larger than key_length.

        :param val: The values to be checked
        """
        m_val = max(len(v) for v in val)
        if m_val > self.exec.key_length:
            raise ValueError(
                f'{self.exec} allows only keys of length {self.exec.key_length}, '
                f'but yours is {m_val}.'
            )


class VectorIndexDriver(BaseIndexDriver):
    """Extracts embeddings and ids from the documents and forwards them to the executor.
    In case `method` is 'delete', the embeddings are ignored.
    If `method` is not 'delete', documents without content are filtered out.
    """

    @property
    def exec_embedding_cls_type(self) -> str:
        """Get the sparse class type of the attached executor.

        :return: Embedding class type of the attached executor, default value is `dense`
        """
        return self.exec.embedding_cls_type

    def _get_documents_embeddings(self, docs: 'DocumentSet'):
        embedding_cls_type = self.exec_embedding_cls_type
        if embedding_cls_type == 'dense':
            return docs.all_embeddings
        else:
            scipy_cls_type = None
            if embedding_cls_type.startswith('scipy'):
                scipy_cls_type = embedding_cls_type.split('_')[1]
                embedding_cls_type = 'scipy'

            return docs.get_all_sparse_embeddings(
                sparse_cls_type=embedding_cls_type, scipy_cls_type=scipy_cls_type
            )

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        embed_vecs, docs_pts = self._get_documents_embeddings(docs)
        if docs_pts:
            keys = [doc.id for doc in docs_pts]
            self.check_key_length(keys)
            self.exec_fn(keys, embed_vecs)


class KVIndexDriver(BaseIndexDriver):
    """Forwards pairs of serialized documents and ids to the executor."""

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        info = [(doc.id, doc.SerializeToString()) for doc in docs]
        if info:
            keys, values = zip(*info)
            self.check_key_length(keys)
            self.exec_fn(keys, values)
