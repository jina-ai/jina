import numpy as np
import pytest
import torch
from docarray import Document, DocumentArray

from jina import Executor, Flow, requests


class MyExec(Executor):
    @requests
    def foo(self, docs, **kwargs):
        pass


class ListInExec(Executor):
    @requests
    def check_list(self, docs, **kwargs):
        embedding_is_list = True
        tensor_is_list = True
        for doc in docs:
            embedding_is_list = embedding_is_list and isinstance(doc.embedding, list)
            tensor_is_list = tensor_is_list and isinstance(doc.tensor, list)
        for doc in docs:
            doc.tags['listcheck_embedding'] = embedding_is_list
            doc.tags['listcheck_tensor'] = tensor_is_list


class NparrayInEec(Executor):
    @requests
    def check_nparray(self, docs, **kwargs):
        embedding_is_nparray = True
        tensor_is_nparray = True
        for doc in docs:
            embedding_is_nparray = embedding_is_nparray and isinstance(
                doc.embedding, np.ndarray
            )
            tensor_is_nparray = tensor_is_nparray and isinstance(doc.tensor, np.ndarray)
        for doc in docs:
            doc.tags['nparraycheck_embedding'] = embedding_is_nparray
            doc.tags['nparraycheck_tensor'] = tensor_is_nparray


@pytest.fixture()
def linear_flow():
    f = (
        Flow()
        .add(uses=MyExec, output_array_type='numpy')
        .add(uses=NparrayInEec, output_array_type='list')
        .add(uses=ListInExec)
    )
    return f


def test_array_conversion(linear_flow):
    docs = DocumentArray.empty(5)
    for doc in docs:
        doc.embedding = torch.tensor(np.random.randn(5))
        doc.tensor = torch.tensor(np.random.randn(3, 3))

    with linear_flow as f:
        resp = f.post(on='/foo', inputs=docs)
    for doc in resp:
        assert doc.tags['nparraycheck_embedding']
        assert doc.tags['nparraycheck_tensor']
        assert doc.tags['listcheck_embedding']
        assert doc.tags['listcheck_tensor']


def test_empty_arrays(linear_flow):
    docs = DocumentArray.empty(5)

    with linear_flow as f:
        resp = f.post(on='/foo', inputs=docs)
    for doc in resp:
        assert not doc.tags['listcheck_embedding']
        assert not doc.tags['listcheck_tensor']
        assert not doc.tags['nparraycheck_embedding']
        assert not doc.tags['nparraycheck_tensor']
