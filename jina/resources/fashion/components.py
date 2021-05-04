from typing import Tuple, Dict

import numpy as np

from jina import Executor, DocumentArray, requests, Document


class MyIndexer(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._docs = DocumentArray()

    @requests(on='/index')
    def index(self, docs: 'DocumentArray', **kwargs):
        self._docs.extend(docs)

    @requests(on='/search')
    def search(self, docs: 'DocumentArray', parameters: Dict, **kwargs):
        q_emb = _ext_A(_norm(docs.all_embeddings[0]))
        d_emb = _ext_B(_norm(self._docs.all_embeddings[0]))
        dists = _cosine(q_emb, d_emb)
        idx, dist = self._get_sorted_top_k(dists, int(parameters['top_k']))
        for _q, _ids, _dists in zip(docs, idx, dist):
            for _id, _dist in zip(_ids, _dists):
                d = Document(self._docs[int(_id)], copy=True)
                d.score.value = 1 - _dist
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


class MyEncoder(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        np.random.seed(1337)
        # generate a random orthogonal matrix
        H = np.random.rand(784, 64)
        u, s, vh = np.linalg.svd(H, full_matrices=False)
        self.oth_mat = u @ vh

    @requests
    def encode(self, docs: 'DocumentArray', **kwargs):
        # reduce dimension to 50 by random orthogonal projection
        content, doc_pts = docs.all_contents
        embeds = (content.reshape([-1, 784]) / 255) @ self.oth_mat
        for doc, embed in zip(doc_pts, embeds):
            doc.embedding = embed
            doc.convert_blob_to_uri(width=28, height=28)
            doc.pop('blob')


def _get_ones(x, y):
    return np.ones((x, y))


def _ext_A(A):
    nA, dim = A.shape
    A_ext = _get_ones(nA, dim * 3)
    A_ext[:, dim: 2 * dim] = A
    A_ext[:, 2 * dim:] = A ** 2
    return A_ext


def _ext_B(B):
    nB, dim = B.shape
    B_ext = _get_ones(dim * 3, nB)
    B_ext[:dim] = (B ** 2).T
    B_ext[dim: 2 * dim] = -2.0 * B.T
    del B
    return B_ext


def _euclidean(A_ext, B_ext):
    sqdist = A_ext.dot(B_ext).clip(min=0)
    return np.sqrt(sqdist)


def _norm(A):
    return A / np.linalg.norm(A, ord=2, axis=1, keepdims=True)


def _cosine(A_norm_ext, B_norm_ext):
    return A_norm_ext.dot(B_norm_ext).clip(min=0) / 2
