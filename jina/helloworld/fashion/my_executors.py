from typing import Dict

import numpy as np
from jina import Executor, DocumentArray, requests
from jina import DocumentArrayMemmap


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
        docs.match(
            self._docs,
            metric='cosine',
            normalization=(1, 0),
            limit=int(parameters['top_k']),
        )


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
        content = content[:, :, :, 0].reshape(-1, 784)
        embeds = ((content / 255) @ self.oth_mat).astype(np.float32)
        for doc, embed, cont in zip(docs, embeds, content):
            doc.embedding = embed
            doc.content = cont
            doc.convert_image_blob_to_uri()
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
            doc.convert_image_blob_to_uri()
            doc.pop('blob')


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
