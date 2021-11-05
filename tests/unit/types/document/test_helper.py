import types

import numpy as np
import pytest
import tensorflow
import torch
from scipy.sparse import csr_matrix
from tensorflow import SparseTensor

from jina import Document
from jina.proto.jina_pb2 import DenseNdArrayProto, SparseNdArrayProto
from jina.types.document import _get_array_type
from jina.types.document.helper import DocGroundtruthPair
from jina.types.ndarray.generic import NdArray


@pytest.fixture(scope='function')
def document_factory():
    class DocumentFactory(object):
        def create(self, content):
            return Document(content=content)

    return DocumentFactory()


@pytest.fixture(scope='function')
def chunks(document_factory):
    return [
        document_factory.create('test chunk 1'),
        document_factory.create('test chunk 2'),
        document_factory.create('test chunk 3'),
    ]


@pytest.fixture(scope='function')
def matches(document_factory):
    return [
        document_factory.create('test match 1'),
        document_factory.create('test match 2'),
        document_factory.create('test match 3'),
    ]


@pytest.fixture(scope='function')
def document(document_factory, chunks, matches):
    doc = document_factory.create('test document')
    doc.chunks.extend(chunks)
    doc.matches.extend(matches)
    return doc


@pytest.fixture(scope='function')
def groundtruth(document_factory, chunks, matches):
    gt = document_factory.create('test groundtruth')
    gt.chunks.extend(chunks)
    gt.matches.extend(matches)
    return gt


def test_init(document, groundtruth):
    assert DocGroundtruthPair(doc=document, groundtruth=groundtruth)


def test_matches_success(document, groundtruth):
    pair = DocGroundtruthPair(doc=document, groundtruth=groundtruth)
    assert isinstance(pair.matches, types.GeneratorType)
    for _ in pair.matches:
        pass


def test_matches_fail(document_factory, document, groundtruth):
    # document and groundtruth not the same length
    groundtruth.matches.append(document_factory.create('test match 4'))
    pair = DocGroundtruthPair(doc=document, groundtruth=groundtruth)
    with pytest.raises(AssertionError):
        for _ in pair.matches:
            pass


def test_chunks_success(document, groundtruth):
    pair = DocGroundtruthPair(doc=document, groundtruth=groundtruth)
    assert isinstance(pair.chunks, types.GeneratorType)
    for _ in pair.chunks:
        pass


def test_chunks_fail(document_factory, document, groundtruth):
    # document and groundtruth not the same length
    groundtruth.chunks.append(document_factory.create('test chunk 4'))
    pair = DocGroundtruthPair(doc=document, groundtruth=groundtruth)
    with pytest.raises(AssertionError):
        for _ in pair.chunks:
            pass


@pytest.mark.parametrize(
    'array, expect',
    [
        (np.array([1, 2, 3]), ('numpy', False)),
        (tensorflow.constant([[1.0, 2.0], [3.0, 4.0]]), ('tensorflow', False)),
        (torch.Tensor([1, 2, 3]), ('torch', False)),
        (
            SparseTensor(indices=[[0, 0], [1, 2]], values=[1, 2], dense_shape=[3, 4]),
            ('tensorflow', True),
        ),
        (csr_matrix([0, 0, 0, 1, 0]), ('scipy', True)),
        (
            torch.sparse_coo_tensor([[0, 1, 1], [2, 0, 2]], [3, 4, 5], (2, 3)),
            ('torch', True),
        ),
        (NdArray(np.random.random([3, 5])), ('jina', False)),
        (DenseNdArrayProto(), ('jina_proto', False)),
        (SparseNdArrayProto(), ('jina_proto', True)),
    ],
)
def test_get_array_type(array, expect):
    _get_array_type(array) == expect
