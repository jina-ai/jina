import numpy as np

from jina import Executor, requests, DocumentArray


class MyEncoder(Executor):
    """Simple Encoder used in :command:`jina hello-world`,
    it transforms the original 784-dim vector into a 64-dim vector using
    a random orthogonal matrix, which is stored and shared in index and query time"""

    def __init__(self):
        np.random.seed(1337)
        # generate a random orthogonal matrix
        H = np.random.rand(784, 64)
        u, s, vh = np.linalg.svd(H, full_matrices=False)
        self.oth_mat = u @ vh

    @requests
    def encode(self, docs: 'DocumentArray', **kwargs):
        # reduce dimension to 50 by random orthogonal projection
        content, doc_pts = docs.all_contents
        embeds = (content.reshape([-1, 784]) / 255) @ self.oth_mat
        for doc, embed in zip(doc_pts, embeds):
            doc.embedding = embed
            doc.convert_blob_to_uri(width=28, height=28)
            doc.pop('blob')
