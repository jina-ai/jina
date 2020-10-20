import numpy as np

from ..embedding import BaseEmbeddingEvaluator, expand_vector
from ...indexers.vector import _euclidean, _ext_A, _ext_B, _cosine, _norm


class CosineEvaluator(BaseEmbeddingEvaluator):
    """A :class:`CosineEvaluator` evaluates the distance between doc and groundtruth embeddings computing
    the cosine distance between them. (The smaller value the closest distance, it is not cosine similarity measure)

    .. math::

        1 - \\frac{u \\cdot v}
                  {||u||_2 ||v||_2}.
    """

    @property
    def metric(self):
        return 'CosineDistance'

    def evaluate(self, actual: 'np.array', desired: 'np.array', *args, **kwargs) -> float:
        """"
        :param actual: the embedding of the document (resulting from an Encoder)
        :param desired: the expected embedding of the document
        :return the evaluation metric value for the request document
        """
        actual = expand_vector(actual)
        desired = expand_vector(desired)
        return _cosine(_ext_A(_norm(actual)), _ext_B(_norm(desired)))
