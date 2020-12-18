__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Sequence, Any

import numpy as np

from ..executors.encoders import BaseImageEncoder
from ..executors.evaluators.rank import BaseRankingEvaluator


class MyEncoder(BaseImageEncoder):
    """Simple Encoder used in :command:`jina hello-world`,
        it transforms the original 784-dim vector into a 64-dim vector using
        a random orthogonal matrix, which is stored and shared in index and query time"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        np.random.seed(1337)
        # generate a random orthogonal matrix
        H = np.random.rand(784, 64)
        u, s, vh = np.linalg.svd(H, full_matrices=False)
        self.oth_mat = u @ vh
        self.touch()

    def encode(self, data: 'np.ndarray', *args, **kwargs):
        # reduce dimension to 50 by random orthogonal projection
        return (data.reshape([-1, 784]) / 255) @ self.oth_mat


class MyEvaluator(BaseRankingEvaluator):
    """MyEvaluator differs from :class:`PrecisionEvaluator` because it evaluates how many of the returned matches
    are of the same label as the true nearest neighbor
    """

    @property
    def metric(self):
        return f'LabelPrecision@{self.eval_at}'

    def evaluate(self, actual: Sequence[Any], desired: Sequence[Any], *args, **kwargs) -> float:
        desired_label = desired[0]

        ret = 0.0
        for match_label in actual[:self.eval_at]:
            if match_label == desired_label:
                ret += 1.0

        divisor = min(self.eval_at, len(actual))
        return ret / divisor if divisor != 0.0 else 0.0
