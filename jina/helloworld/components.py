__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from ..executors.crafters import BaseSegmenter
from ..executors.encoders import BaseImageEncoder


class MySegmenter(BaseSegmenter):
    """Simple Segementer used in :command:`jina hello-world`,
    each doc contains only one chunk """

    def craft(self, blob, *args, **kwargs):
        return [dict(blob=blob)]


class MyEncoder(BaseImageEncoder):
    """Simple Encoder used in :command:`jina hello-world`,
        it transforms the original 784-dim vector into a 64-dim vector using
        a random orthogonal matrix, which is stored and shared in index and query time"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # generate a random orthogonal matrix
        H = np.random.rand(784, 64)
        u, s, vh = np.linalg.svd(H, full_matrices=False)
        self.oth_mat = u @ vh
        self.touch()

    def encode(self, data: 'np.ndarray', *args, **kwargs):
        # reduce dimension to 50 by random orthogonal projection
        return (data.reshape([-1, 784]) / 255) @ self.oth_mat
