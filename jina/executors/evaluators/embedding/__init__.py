__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from .. import BaseEvaluator


class BaseEmbeddingEvaluator(BaseEvaluator):
    """A :class:`BaseEmbeddingEvaluator` evaluates the difference between doc and groundtruth embeddings
    """

    def evaluate(self, prediction: 'np.array', groundtruth: 'np.array', *args, **kwargs) -> float:
        """"
        :param prediction: the embedding of the document (resulting from an Encoder)
        :param groundtruth: the expected embedding of the document
        :return the evaluation metric value for the request document
        """
        raise NotImplementedError
