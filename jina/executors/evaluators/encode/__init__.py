__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from .. import BaseEvaluator


class BaseEncodingEvaluator(BaseEvaluator):
    """A :class:`BaseEncodingEvaluator` evaluates the difference between doc and groundtruth embeddings
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def evaluate(self, doc_embedding: 'np.array', groundtruth_embedding: 'np.array', *args, **kwargs) -> float:
        """"
        :param doc_embedding: the embedding of the document (resulting from an Encoder)
        :param groundtruth_embedding: the expected embedding of the document
        :return the evaluation metric value for the request document
        """
        raise NotImplementedError
