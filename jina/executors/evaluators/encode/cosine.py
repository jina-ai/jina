import numpy as np

from ..decorators import as_aggregator
from ..encode import BaseEncodingEvaluator


class CosineEvaluator(BaseEncodingEvaluator):
    """A :class:`CosineEvaluator` evaluates the distance between doc and groundtruth embeddings computing
    the cosine distance between them. (The smaller value the closest distance, it is not cosine similarity measure)

    .. math::

        1 - \\frac{u \\cdot v}
                  {||u||_2 ||v||_2}.
    """

    @property
    def metric(self):
        return f'CosineDistance'

    @as_aggregator
    def evaluate(self, doc_embedding: 'np.array', groundtruth_embedding: 'np.array', *args, **kwargs) -> float:
        """"
        :param doc_embedding: the embedding of the document (resulting from an Encoder)
        :param groundtruth_embedding: the expected embedding of the document
        :return the evaluation metric value for the request document
        """
        from scipy.spatial.distance import cosine
        return cosine(doc_embedding, groundtruth_embedding)
