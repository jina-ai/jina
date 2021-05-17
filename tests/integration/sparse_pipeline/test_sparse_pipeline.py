from typing import Any, Iterable
import os

import pytest
import numpy as np
from scipy import sparse

from jina import Flow, Document, DocumentArray, requests, Executor

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


class DummyCSRSparseIndexEncoder(Executor):
    embedding_cls_type = 'scipy_csr'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs = []
        self.vectors = {}

    @requests(on='index')
    def encode(self, docs: 'DocumentArray', *args, **kwargs) -> Any:
        for doc in docs:
            doc.embedding = sparse.csr_matrix(doc.content)

    @requests(on='index')
    def add(self, docs: 'DocumentArray', *args, **kwargs) -> None:
        self.docs.extend(docs)
        for i, doc in enumerate(docs):
            self.vectors[doc.id] = doc.embedding.getrow(i)  # vectors.getrow(i)

    @requests(on='search')
    def query(self, parameters, *args, **kwargs):
        top_k = parameters['top_k']
        doc = parameters['doc']
        distances = [item for item in range(0, min(top_k, len(self.docs)))]
        return [self.docs[:top_k]], np.array([distances])

    '''
    def query_by_key(self, keys: Iterable[str], *args, **kwargs):
        from scipy.sparse import vstack

        vectors = []
        for key in keys:
            vectors.append(self.vectors[key])

        return vstack(vectors)
    '''

    def save(self):
        # avoid creating dump, do not polute workspace
        pass

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
        Flow().add(uses=DummyCSRSparseIndexEncoder)
        # .add(uses=os.path.join(cur_dir, 'indexer.yml'))
    )

    mock = mocker.Mock()
    error_mock = mocker.Mock()

    with f:
        f.post(on='index', inputs=docs_to_index)
        f.post(
            on='search',
            inputs=docs_to_index[0],
            parameters={'doc': docs_to_index[0], 'top_k': 1},
            on_done=mock,
            on_error=error_mock,
        )

    mock.assert_called_once()
    validate_callback(mock, validate)
    error_mock.assert_not_called()
