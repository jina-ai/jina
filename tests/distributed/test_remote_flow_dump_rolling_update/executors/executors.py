import os

from typing import Optional

import numpy as np
from jina import Executor, requests, DocumentArray, Document
from jina.logging.logger import JinaLogger


class KeyValueDBMSIndexer(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = DocumentArray()
        self.logger = JinaLogger('KeyValueDBMSIndexer')

    @requests(on='/index')
    def index(self, docs: 'DocumentArray', *args, **kwargs):
        self._docs.extend(docs)

    # TODO endpoint in tests.distributed.test_remote_flow_dump_rolling_update.test_dump_dbms_remote.test_dump_dbms_remote
    # ends up being http://0.0.0.0:9000/post/dump
    @requests(on='/dump')
    def dump(self, parameters, *args, **kwargs):
        dump_path = parameters['dump_path']
        # TODO: maybe put some logic for shards here
        self._docs.save(dump_path)


class CompoundQueryExecutor(Executor):
    def __init__(self, dump_path: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = JinaLogger('CompoundQueryExecutor')
        self._dump_path = dump_path
        if self._dump_path is not None and os.path.exists(self._dump_path):
            self._docs = DocumentArray.load(self._dump_path)
        else:
            self._docs = DocumentArray()

    @staticmethod
    def _get_sorted_top_k(dist: 'np.array', top_k: int):
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

    @requests(on='/search')
    def search(self, docs: 'DocumentArray', parameters, **kwargs):
        if len(self._docs) > 0:
            a = np.stack(docs.get_attributes('embedding'))
            b = np.stack(self._docs.get_attributes('embedding'))
            q_emb = _ext_A(_norm(a))
            d_emb = _ext_B(_norm(b))
            dists = _cosine(q_emb, d_emb)
            idx, dist = self._get_sorted_top_k(dists, int(parameters['top_k']))
            for _q, _ids, _dists in zip(docs, idx, dist):
                for _id, _dist in zip(_ids, _dists):
                    d = Document(self._docs[int(_id)], copy=True)
                    d.scores['cosine'] = 1 - _dist
                    _q.matches.append(d)


def _get_ones(x, y):
    return np.ones((x, y))


def _ext_A(A):
    nA, dim = A.shape
    A_ext = _get_ones(nA, dim * 3)
    A_ext[:, dim : 2 * dim] = A
    A_ext[:, 2 * dim :] = A ** 2
    return A_ext


def _ext_B(B):
    nB, dim = B.shape
    B_ext = _get_ones(dim * 3, nB)
    B_ext[:dim] = (B ** 2).T
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


class MergeMatchesExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = JinaLogger('MergeMatchesExecutor')

    @requests
    def merge(self, *args, **kwargs):
        pass
