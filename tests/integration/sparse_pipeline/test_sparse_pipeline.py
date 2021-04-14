from typing import Any, Iterable

import pytest
import numpy as np
from scipy import sparse

from jina import Flow, Document
from jina.types.sets import DocumentSet
from jina.executors.encoders import BaseEncoder
from jina.executors.indexers import BaseSparseVectorIndexer


@pytest.fixture(scope='function')
def num_docs():
    return 10


@pytest.fixture(scope='function')
def docs_to_index(num_docs):
    docs = []
    for idx in range(1, num_docs + 1):
        doc = Document(content=np.array([idx]))
        docs.append(doc)
    return DocumentSet(docs)


class DummySparseEncoder(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def encode(self, data: Any, *args, **kwargs) -> Any:
        embed = sparse.csr_matrix(data)
        return embed


class DummyCSRSparseIndexer(BaseSparseVectorIndexer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keys = []

    def add(
        self, keys: Iterable[str], vectors: 'scipy.sparse.coo_matrix', *args, **kwargs
    ) -> None:
        assert isinstance(vectors, sparse.coo_matrix)
        self.keys.extend(keys)

    def query(self, vectors: 'scipy.sparse.coo_matrix', top_k: int, *args, **kwargs):
        assert isinstance(vectors, sparse.coo_matrix)
        distances = [item for item in range(0, min(top_k, len(self.keys)))]

        return np.array(self.keys[:top_k]), np.array([distances])

    def get_create_handler(self):
        pass

    def get_write_handler(self):
        pass

    def get_add_handler(self):
        pass

    def get_query_handler(self):
        pass


def test_sparse_pipeline(mocker, docs_to_index):
    def validate(response):
        assert len(response.docs) == 10

    f = Flow().add(uses=DummySparseEncoder).add(uses=DummyCSRSparseIndexer)

    error_mock = mocker.Mock()

    with f:
        f.index(inputs=docs_to_index)
        f.search(inputs=docs_to_index, on_done=validate, on_error=error_mock)

    error_mock.assert_not_called()
