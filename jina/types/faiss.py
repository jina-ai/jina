from copy import copy
from typing import Optional
from typing import Tuple

import faiss
import numpy as np

from .arrays import DocumentArray
from .. import Document

# if metric requires embeddings normalization
NORMALIZE_METRIC = {
    'cosine': True
}

class FaissIndexer:
    """
    Create a indexer for fast similarity search using Faiss (https://github.com/facebookresearch/faiss).
    The embeddings are stored in a flat array and the similarity computation is performed using several
    optimization such as clustering.
    This indexer allows only append operation (not insertion).
    """

    def __init__(self, docs: Optional[DocumentArray] = None, use_for_metric: str = 'cosine'):
        """
        Create the Faiss indexer

        :param docs: Optional array of documents to store inside the indexer
        :param use_for_metric: The metric to use for searching inside the indexer
        """
        #TODO: implement new metrics and new type of indicies (right now only Flat possible)
        if use_for_metric != 'cosine':
            raise NotImplementedError('Metrics but cosine are not yet implemented')
        self._index     = None
        self._metric    = use_for_metric
        self._normalize = NORMALIZE_METRIC[use_for_metric]
        self._docs      = []
        if docs is not None:
            self._init_indexer(emb_size=docs[0].embedding.shape[-1])
            self.extend(docs)

    def append(self, doc: Document):
        """
        Append a document to the indexer.

        :param doc: the document to append.
        """
        #TODO: think about inserting a copy of the document
        self._docs.append(doc)
        assert hasattr(doc, 'embedding')
        self._append_embedding(doc.embedding)

    def extend(self, docs: DocumentArray):
        """
        Append a series of documents.

        :params docs: The series of documents to append.
        """
        for doc in docs:
            self.append(doc)

    def search(self, query: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Retrieve the top-k elements inside the indexer.

        :params query: The query embedding.
        :params k: the number of elements to retrieve.
        :return: distances and indices
        """
        query_cpy = copy(query)
        if self._normalize:
            faiss.normalize_L2(query_cpy)
        sim, idx = self._index.search(query_cpy, k)
        # cosine_dist = 1-cosine_sim
        return 1-np.clip(sim, -1, 1), idx

    def _init_indexer(self, emb_size: int):
        """
        Initialize the Faiss indexer.

        :params emb_size: The size of the embeddings to store.
        """
        self._emb_size = emb_size
        self._index    = faiss.index_factory(emb_size, "Flat", faiss.METRIC_INNER_PRODUCT)

    def _append_embedding(self, embedding: np.ndarray):
        """
        Append an embedding to the Faiss indexer.

        :params embedding: The embedding to append.
        """
        if self._index is None:
            self._init_indexer(emb_size=embedding.shape[-1])
        embedding_cpy = embedding.reshape(1, -1) #make a copy
        if self._normalize:
            faiss.normalize_L2(embedding_cpy)
        self._index.add(embedding_cpy)

    def __len__(self) -> int:
        """
        Get the number of documents currently stored in the indexer.

        :return: the number of documents
        """
        if self._index is None:
            return 0
        return self._index.ntotal

    def __getitem__(self, idx: int):
        """
        Get the i-th document in the indexer.

        :params idx: Index of the document to retrieve (0-indexed).
        """
        return self._docs[idx]

    @property
    def embeddings_size(self) -> int:
        """
        Get the size of the embeddings.

        :return: the size of the embeddings
        """
        return self._emb_size

    @property
    def metric(self) -> str:
        """
        Get the distance metric used for the similarity search.

        :return: the distance metric used
        """
        return self._metric