from typing import Any, Iterable
import os

import pytest
import numpy as np
from scipy import sparse

from jina import Flow, Document, Executor, DocumentArray, requests

# from jina.executors.encoders import BaseEncoder
# from jina.executors.indexers import BaseVectorIndexer

from tests import validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='function')
def num_docs():
    return 10


@pytest.fixture(scope='function')
def docs_to_index(num_docs):
    docs = []
    for idx in range(1, num_docs + 1):
        doc = Document(id=str(idx), content=np.array([idx * 5]))
        docs.append(doc)
    return DocumentArray(docs)


class DummySparseEncoder(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def encode(self, content: 'np.ndarray', *args, **kwargs) -> Any:
        embed = sparse.csr_matrix(content)
        return embed


class DummyCSRSparseIndexer(Executor):
    embedding_cls_type = 'scipy_csr'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keys = []
        self.vectors = {}

    def add(
        self, keys: Iterable[str], vectors: 'scipy.sparse.csr_matrix', *args, **kwargs
    ) -> None:
        assert isinstance(vectors, sparse.csr_matrix)
        self.keys.extend(keys)
        for i, key in enumerate(keys):
            self.vectors[key] = vectors.getrow(i)

    @requests(on='search')
    def query(self, vectors: 'scipy.sparse.csr_matrix', top_k: int, *args, **kwargs):
        assert isinstance(vectors, sparse.csr_matrix)
        distances = [item for item in range(0, min(top_k, len(self.keys)))]
        return [self.keys[:top_k]], np.array([distances])

    def query_by_key(self, keys: Iterable[str], *args, **kwargs):
        from scipy.sparse import vstack

        vectors = []
        for key in keys:
            vectors.append(self.vectors[key])

        return vstack(vectors)

    @requests(on='index')
    def save(self, docs: 'DocumentArray', **kwargs):
        # avoid creating dump, do not polute workspace
        self.vectors = docs

    def close(self):
        # avoid creating dump, do not polute workspace
        pass

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
        assert len(response.docs) == 1
        assert len(response.docs[0].matches) == 10
        for doc in response.docs:
            for i, match in enumerate(doc.matches):
                assert match.id == docs_to_index[i].id
                assert isinstance(match.embedding, sparse.coo_matrix)

    f = (
        Flow().add(uses=DummySparseEncoder)
        # add(uses=os.path.join(cur_dir, 'indexer.yml'))
    )

    mock = mocker.Mock()
    error_mock = mocker.Mock()

    with f:
        f.post(on='index', inputs=docs_to_index)
        f.post(on='search', inputs=docs_to_index[0], on_done=mock, on_error=error_mock)

    mock.assert_called_once()
    validate_callback(mock, validate)
    error_mock.assert_not_called()
