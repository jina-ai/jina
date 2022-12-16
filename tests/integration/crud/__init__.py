import os
from typing import Dict, Tuple

import numpy as np

from docarray import Document, DocumentArray, Executor, requests
from jina.logging.logger import JinaLogger


class CrudIndexer(Executor):
    """Simple indexer class"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = JinaLogger('CrudIndexer')
        self._docs = DocumentArray()
        self._dump_location = os.path.join(self.metas.workspace, 'docs.json')
        if os.path.exists(self._dump_location):
            self._docs = DocumentArray.load_json(self._dump_location)
            self.logger.debug(f'Loaded {len(self._docs)} from {self._dump_location}')
        else:
            self.logger.warning(f'No data found at {self._dump_location}')

    @requests(on='/index')
    def index(self, docs: 'DocumentArray', **kwargs):
        self._docs.extend(docs)

    @requests(on='/update')
    def update(self, docs: 'DocumentArray', **kwargs):
        self.delete(docs)
        self.index(docs)

    def close(self) -> None:
        self.logger.debug(f'Dumping {len(self._docs)} to {self._dump_location}')
        self._docs.save_json(self._dump_location)

    @requests(on='/delete')
    def delete(self, docs: 'DocumentArray', **kwargs):
        # TODO we can do del _docs[d.id] once
        # tests.unit.types.arrays.test_documentarray.test_delete_by_id is fixed
        ids_to_delete = [d.id for d in docs]
        idx_to_delete = []
        for i, doc in enumerate(self._docs):
            if doc.id in ids_to_delete:
                idx_to_delete.append(i)
        for i in sorted(idx_to_delete, reverse=True):
            del self._docs[i]

    @requests(on='/search')
    def search(self, docs: 'DocumentArray', parameters: Dict, **kwargs):
        top_k = int(parameters.get('top_k', 1))
        a = np.stack(docs[:, 'embedding'])
        b = np.stack(self._docs[:, 'embedding'])
        q_emb = _ext_A(_norm(a))
        d_emb = _ext_B(_norm(b))
        dists = _cosine(q_emb, d_emb)
        idx, dist = self._get_sorted_top_k(dists, top_k)
        for _q, _ids, _dists in zip(docs, idx, dist):
            for _id, _dist in zip(_ids, _dists):
                d = Document(self._docs[int(_id)], copy=True)
                d.scores['cosine'].value = 1 - _dist
                _q.matches.append(d)

    @staticmethod
    def _get_sorted_top_k(
        dist: 'np.array', top_k: int
    ) -> Tuple['np.ndarray', 'np.ndarray']:
        if top_k >= dist.shape[1]:
            idx = dist.argsort(axis=1)[:, :top_k]
            dist = np.take_along_axis(dist, idx, axis=1)
        else:
            idx_ps = dist.argpartition(kth=top_k, axis=1)[:, :top_k]
            dist = np.take_along_axis(dist, idx_ps, axis=1)
            idx_fs = dist.argsort(axis=1)
            idx = np.take_along_axis(idx_ps, idx_fs, axis=1)
            dist = np.take_along_axis(dist, idx_fs, axis=1)

        return idx, dist


def _get_ones(x, y):
    return np.ones((x, y))


def _ext_A(A):
    nA, dim = A.shape
    A_ext = _get_ones(nA, dim * 3)
    A_ext[:, dim : 2 * dim] = A
    A_ext[:, 2 * dim :] = A**2
    return A_ext


def _ext_B(B):
    nB, dim = B.shape
    B_ext = _get_ones(dim * 3, nB)
    B_ext[:dim] = (B**2).T
    B_ext[dim : 2 * dim] = -2.0 * B.T
    del B
    return B_ext


def _euclidean(A_ext, B_ext):
    sqdist = A_ext.dot(B_ext).clip(min=0)
    return np.sqrt(sqdist)


def _norm(A):
    return A / np.linalg.norm(A, ord=2, axis=1, keepdims=True)


def _cosine(A_norm_ext, B_norm_ext):
    return A_norm_ext.dot(B_norm_ext).clip(min=0) / 2
