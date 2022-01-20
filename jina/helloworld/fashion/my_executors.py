import os
from typing import Dict

import numpy as np
from jina import Executor, requests
from docarray import DocumentArray


class MyIndexer(Executor):
    """
    Executor with basic exact search using cosine distance
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if os.path.exists(self.workspace + '/indexer'):
            self._docs = DocumentArray.load(self.workspace + '/indexer')
        else:
            self._docs = DocumentArray()

    @requests(on='/index')
    def index(self, docs: 'DocumentArray', **kwargs):
        """Extend self._docs

        :param docs: DocumentArray containing Documents
        :param kwargs: other keyword arguments
        """
        self._docs.extend(docs)

    @requests(on=['/search', '/eval'])
    def search(self, docs: 'DocumentArray', parameters: Dict, **kwargs):
        """Append best matches to each document in docs

        :param docs: documents that are searched
        :param parameters: dictionary of pairs (parameter,value)
        :param kwargs: other keyword arguments
        """
        docs.match(
            self._docs,
            metric='cosine',
            normalization=(1, 0),
            limit=int(parameters['top_k']),
        )

    def close(self):
        """
        Stores the DocumentArray to disk
        """
        self._docs.save(self.workspace + '/indexer')


class MyEncoder(Executor):
    """
    Encode data using SVD decomposition
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        np.random.seed(1337)
        # generate a random orthogonal matrix
        H = np.random.rand(784, 64)
        u, s, vh = np.linalg.svd(H, full_matrices=False)
        self.oth_mat = u @ vh

    @requests
    def encode(self, docs: 'DocumentArray', **kwargs):
        """Encode the data using an SVD decomposition

        :param docs: input documents to update with an embedding
        :param kwargs: other keyword arguments
        """
        # reduce dimension to 50 by random orthogonal projection
        content = np.stack(docs[:, 'content'])
        content = content[:, :, :, 0].reshape(-1, 784)
        embeds = ((content / 255) @ self.oth_mat).astype(np.float32)
        for doc, embed, cont in zip(docs, embeds, content):
            doc.embedding = embed
            doc.content = cont
            doc.convert_image_tensor_to_uri()
            doc.pop('tensor')


class MyConverter(Executor):
    """
    Convert DocumentArrays removing tensor and reshaping tensor as image
    """

    @requests
    def convert(self, docs: 'DocumentArray', **kwargs):
        """
        Remove tensor and reshape documents as squared images
        :param docs: documents to modify
        :param kwargs: other keyword arguments
        """
        for doc in docs:
            doc.convert_image_tensor_to_uri()
            doc.pop('tensor')
