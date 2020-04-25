__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from ..executors.crafters import BaseSegmenter, BaseDocCrafter
from ..executors.encoders import BaseImageEncoder


class MyDocCrafter(BaseDocCrafter):
    """Simple DocCrafter used in :command:`jina hello-world`,
    it reads ``raw_bytes`` into base64 png and stored in ``meta_info``"""

    def craft(self, raw_bytes, *args, **kwargs):
        doc = np.frombuffer(raw_bytes, dtype=np.uint8)
        from .helper import write_png
        return dict(meta_info=write_png(doc))


class MySegmenter(BaseSegmenter):
    """Simple Segementer used in :command:`jina hello-world`,
    each doc contains only one chunk """

    def craft(self, raw_bytes, doc_id, *args, **kwargs):
        return [dict(blob=np.frombuffer(raw_bytes, dtype=np.uint8))]


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
