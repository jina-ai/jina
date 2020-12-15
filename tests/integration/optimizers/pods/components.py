__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from jina.executors.encoders import BaseImageEncoder
from jina.optimizers.parameters import IntegerParameter


class MyEncoder(BaseImageEncoder):
    """Simple Encoder used in :command:`jina hello-world`,
        it transforms the original 784-dim vector into a 64-dim vector using
        a random orthogonal matrix, which is stored and shared in index and query time"""

    DEFAULT_OPTIMIZATION_PARAMETER = [
        IntegerParameter(
            executor_name='MyEncoder',
            parameter_name='target_dimension',
            low=32,
            high=256,
            step_size=32
        ),
    ]

    def __init__(self, target_dimension=64, *args, **kwargs):
        super().__init__(*args, **kwargs)
        np.random.seed(1337)
        # generate a random orthogonal matrix
        H = np.random.rand(784, target_dimension)
        u, s, vh = np.linalg.svd(H, full_matrices=False)
        self.oth_mat = u @ vh
        self.touch()

    def encode(self, data: 'np.ndarray', *args, **kwargs):
        # reduce dimension to 50 by random orthogonal projection
        return (data.reshape([-1, 784]) / 255) @ self.oth_mat
#
