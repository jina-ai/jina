import numpy as np

from ..embedding import BaseEmbeddingEvaluator, expand_vector
from ...indexers.vector import _euclidean, _ext_B, _ext_A


class EuclideanEvaluator(BaseEmbeddingEvaluator):
    """A :class:`EuclideanEvaluator` evaluates the distance between actual and desired embeddings computing
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
        actual = expand_vector(actual)
        desired = expand_vector(desired)
        return _euclidean(_ext_A(actual), _ext_B(desired))
