from typing import Tuple, Dict

import numpy as np

from jina import Executor, DocumentArray, requests, Document
from jina.types.arrays.memmap import DocumentArrayMemmap


class MyIndexer(Executor):
    """
    Executor with basic exact search using cosine distance
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._docs = DocumentArrayMemmap(self.workspace + '/indexer')

    @requests(on='/index')
    def index(self, docs: 'DocumentArray', **kwargs):
        """Extend self._docs

        :param docs: DocumentArray containing Documents
        :param kwargs: other keyword arguments
        """
        self._docs.extend(docs)

    @requests(on=['/search', '/eval'])
    def search(self, docs: 'DocumentArray', parameters: Dict, **kwargs):
        """Append best matches to each document in docs

        :param docs: documents that are searched
        :param parameters: dictionary of pairs (parameter,value)
        :param kwargs: other keyword arguments
        """
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

    @staticmethod
    def _get_sorted_top_k(
        dist: 'np.array', top_k: int
    ) -> Tuple['np.ndarray', 'np.ndarray']:
        """Sort and select top k distances
        :param dist: array of distances
        :param top_k: number of values to retrieve
        :return: indices and distances
        """
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
    """
    Encode data using SVD decomposition
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        np.random.seed(1337)
        # generate a random orthogonal matrix
        H = np.random.rand(784, 64)
        u, s, vh = np.linalg.svd(H, full_matrices=False)
        self.oth_mat = u @ vh

    @requests
    def encode(self, docs: 'DocumentArray', **kwargs):
        """Encode the data using an SVD decomposition

        :param docs: input documents to update with an embedding
        :param kwargs: other keyword arguments
        """
        # reduce dimension to 50 by random orthogonal projection
        content = np.stack(docs.get_attributes('content'))
        # content.shape=(request_size, 28, 28, 3)
        content = content[:, :, :, 0].reshape(-1, 784)
        # content.shape=(request_size, 784)
        embeds = (content.reshape([-1, 784]) / 255) @ self.oth_mat
        for doc, embed in zip(docs, embeds):
            doc.embedding = embed
            doc.convert_image_blob_to_uri(width=28, height=28)
            doc.pop('blob')


class MyConverter(Executor):
    """
    Convert DocumentArrays removing blob and reshaping blob as image
    """

    @requests
    def convert(self, docs: 'DocumentArray', **kwargs):
        """
        Remove blob and reshape documents as squared images
        :param docs: documents to modify
        :param kwargs: other keyword arguments
        """
        for doc in docs:
            doc.convert_image_blob_to_uri(width=28, height=28)
            doc.pop('blob')


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


class MyEvaluator(Executor):
    """
    Executor that evaluates precision and recall
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.eval_at = 50
        self.num_docs = 0
        self.total_precision = 0
        self.total_recall = 0

    @property
    def avg_precision(self):
        """
        Computes precision
        :return: precision values
        """
        return self.total_precision / self.num_docs

    @property
    def avg_recall(self):
        """
        Computes recall
        :return: np.ndarray with recall values
        """
        return self.total_recall / self.num_docs

    def _precision(self, actual, desired):
        if self.eval_at == 0:
            return 0.0
        actual_at_k = actual[: self.eval_at] if self.eval_at else actual
        ret = len(set(actual_at_k).intersection(set(desired)))
        sub = len(actual_at_k)
        return ret / sub if sub != 0 else 0.0

    def _recall(self, actual, desired):
        if self.eval_at == 0:
            return 0.0
        actual_at_k = actual[: self.eval_at] if self.eval_at else actual
        ret = len(set(actual_at_k).intersection(set(desired)))
        return ret / len(desired)

    @requests(on='/eval')
    def evaluate(self, docs: 'DocumentArray', groundtruths: 'DocumentArray', **kwargs):
        """Evaluate documents using the class values from ground truths

        :param docs: documents to evaluate
        :param groundtruths: ground truth for the documents
        :param kwargs: other keyword arguments
        """
        for doc, groundtruth in zip(docs, groundtruths):
            self.num_docs += 1
            actual = [match.tags['id'] for match in doc.matches]
            desired = groundtruth.matches[0].tags['id']  # pseudo_match
            self.total_precision += self._precision(actual, desired)
            self.total_recall += self._recall(actual, desired)
            doc.evaluations['Precision'] = self.avg_precision
            doc.evaluations['Precision'].op_name = 'Precision'
            doc.evaluations['Recall'] = self.avg_recall
            doc.evaluations['Recall'].op_name = 'Recall'
