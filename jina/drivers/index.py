__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

import numpy as np

from . import BaseExecutableDriver, FastRecursiveMixin

if False:
    from ..types.sets import DocumentSet


class BaseIndexDriver(FastRecursiveMixin, BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`add` by default """

    def __init__(self, executor: str = None, method: str = 'add', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)

    def check_key_length(self, val: Iterable[str]):
        m_val = max(len(v) for v in val)
        if m_val > self.exec.key_length:
            raise ValueError(f'{self.exec} allows only keys of length {self.exec.key_length}, '
                             f'but yours is {m_val}.')


class VectorIndexDriver(BaseIndexDriver):
    """Extracts embeddings and ids from the documents and forwards them to the executor.
    In case `method` is 'delete', the embeddings are ignored.
    If `method` is not 'delete', documents without content are filtered out.
    """

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        embed_vecs, docs_pts = docs.all_embeddings
        if docs_pts:
            keys = [doc.id for doc in docs_pts]
            self.check_key_length(keys)
            self.exec_fn(keys, np.stack(embed_vecs))


class KVIndexDriver(BaseIndexDriver):
    """Forwards pairs of serialized documents and ids to the executor.
    """

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        info = [(doc.id, doc.SerializeToString()) for doc in docs]
        if info:
            keys, values = zip(*info)
            self.check_key_length(keys)
            self.exec_fn(keys, values)
