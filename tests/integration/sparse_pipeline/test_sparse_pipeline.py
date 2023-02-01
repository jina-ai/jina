import os
from typing import Any

import numpy as np
import pytest
from scipy import sparse

from jina import Document, DocumentArray, Executor, Flow, requests
from tests import validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))
TOP_K = 3


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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs = DocumentArray()

    @requests(on='/index')
    def encode(self, docs: DocumentArray, *args, **kwargs) -> Any:
        for i, doc in enumerate(docs):
            doc.embedding = sparse.coo_matrix(doc.content)
        self.docs.extend(docs)

    @requests(on='/search')
    def query(self, docs: DocumentArray, parameters, *args, **kwargs):
        top_k = int(parameters['top_k'])
        for doc in docs:
            doc.matches = self.docs[:top_k]


def test_sparse_pipeline(mocker, docs_to_index):
    def validate(response):
        assert len(response.docs) == 1
        for doc in response.docs:
            assert len(doc.matches) == TOP_K
            for i, match in enumerate(doc.matches):
                assert match.id == docs_to_index[i].id
                assert isinstance(match.embedding, sparse.coo_matrix)

    f = Flow().add(uses=DummyCSRSparseIndexEncoder)

    mock = mocker.Mock()
    error_mock = mocker.Mock()

    with f:
        f.post(
            on='/index',
            inputs=docs_to_index,
            on_error=error_mock,
        )
        f.post(
            on='/search',
            inputs=docs_to_index[0],
            parameters={'top_k': TOP_K},
            on_done=mock,
            on_error=error_mock,
        )

    mock.assert_called_once()
    validate_callback(mock, validate)
    error_mock.assert_not_called()
