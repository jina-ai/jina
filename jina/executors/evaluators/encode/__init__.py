__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from .. import BaseEvaluator


class BaseEncodingEvaluator(BaseEvaluator):
    """A :class:`BaseEncodingEvaluator` evaluates the distance between doc and groundtruth embeddings
    """

    def __init__(self, *args, **kwargs):
        """"
        :param eval_at: k at which evaluation is performed
        """
        super().__init__(*args, **kwargs)

    def post_init(self):
        super().post_init()
        self.num_documents = 0
        self.sum = 0

    @property
    def avg(self):
        if self.num_documents == 0:
            return 0.0
        return self.sum / self.num_documents

    def evaluate(self, doc_embedding: 'np.array', groundtruth_embedding: 'np.array', *args, **kwargs) -> float:
        """"
        :param doc_embedding: the embedding of the document (resulting from an Encoder)
        :param groundtruth_embedding: the expected embedding of the document
        :return the evaluation metric value for the request document
        """
        raise NotImplementedError
