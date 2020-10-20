import numpy as np

from ..decorators import as_aggregator
from ..embedding import BaseEmbeddingEvaluator


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

    @as_aggregator
    def evaluate(self, prediction: 'np.array', groundtruth: 'np.array', *args, **kwargs) -> float:
        """"
        :param prediction: the embedding of the document (resulting from an Encoder)
        :param groundtruth: the expected embedding of the document
        :return the evaluation metric value for the request document
        """
        from scipy.spatial.distance import cosine
        return cosine(prediction, groundtruth)
