import numpy as np

from ..decorators import as_aggregator
from ..encode import BaseEncodingEvaluator


class EuclideanEvaluator(BaseEncodingEvaluator):
    """A :class:`EuclideanEvaluator` evaluates the distance between doc and groundtruth embeddings computing
    the euclidean distance between them
    """

    @property
    def metric(self):
        return f'EuclideanDistance'

    @as_aggregator
    def evaluate(self, doc_embedding: 'np.array', groundtruth_embedding: 'np.array', *args, **kwargs) -> float:
        """"
        :param doc_embedding: the embedding of the document (resulting from an Encoder)
        :param groundtruth_embedding: the expected embedding of the document
        :return the evaluation metric value for the request document
        """
        from scipy.spatial.distance import euclidean
        return euclidean(doc_embedding, groundtruth_embedding)
