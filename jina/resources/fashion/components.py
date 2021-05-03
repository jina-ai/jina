import numpy as np

from jina import Executor, DocumentArray, requests


class MyEncoder(Executor):
    """Simple Encoder used in :command:`jina hello-world`,
    it transforms the original 784-dim vector into a 64-dim vector using
    a random orthogonal matrix, which is stored and shared in index and query time

    :param width: target width of images
    :param height: target height of images
    """

    def __init__(self, width=28, height=28, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._width = 28
        self._height = 28
        np.random.seed(1337)
        # generate a random orthogonal matrix
        H = np.random.rand(784, 64)
        u, s, vh = np.linalg.svd(H, full_matrices=False)
        self.oth_mat = u @ vh

    @requests
    def encode(self, docs: 'DocumentArray', **kwargs):
        """
        Encode data and reduce dimension

        :param docs: docs array
        :param kwargs: keyword arguments
        :return: encoded data
        """
        # reduce dimension to 50 by random orthogonal projection
        content, doc_pts = docs.all_contents
        embeds = (content.reshape([-1, 784]) / 255) @ self.oth_mat
        for doc, embed in zip(doc_pts, embeds):
            doc.embedding = embed
            doc.convert_blob_to_uri(width=self._width, height=self._height)
            doc.pop('blob')
