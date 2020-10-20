import numpy as np

from ..decorators import as_aggregator
from ..embedding import BaseEmbeddingEvaluator


class EuclideanEvaluator(BaseEmbeddingEvaluator):
    """A :class:`EuclideanEvaluator` evaluates the distance between doc and groundtruth embeddings computing
    the euclidean distance between them
    """

    @property
    def metric(self):
        return 'EuclideanDistance'

    @as_aggregator
    def evaluate(self, prediction: 'np.array', groundtruth: 'np.array', *args, **kwargs) -> float:
        """"
        :param prediction: the embedding of the document (resulting from an Encoder)
        :param groundtruth: the expected embedding of the document
        :return the evaluation metric value for the request document
        """
        from scipy.spatial.distance import euclidean
        return euclidean(prediction, groundtruth)
