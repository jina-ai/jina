import numpy as np

from ..embedding import BaseEmbeddingEvaluator


class EuclideanEvaluator(BaseEmbeddingEvaluator):
    """A :class:`EuclideanEvaluator` evaluates the distance between doc and groundtruth embeddings computing
    the euclidean distance between them
    """

    @property
    def metric(self):
        return 'EuclideanDistance'

    def evaluate(self, actual: 'np.array', desired: 'np.array', *args, **kwargs) -> float:
        """"
        :param actual: the embedding of the document (resulting from an Encoder)
        :param desired: the expected embedding of the document
        :return the evaluation metric value for the request document
        """
        from scipy.spatial.distance import euclidean
        return euclidean(actual, desired)
