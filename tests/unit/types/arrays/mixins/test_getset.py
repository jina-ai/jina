import numpy as np
import pytest
import tensorflow as tf
import torch
from scipy.sparse import csr_matrix

from jina import DocumentArray, Document, DocumentArrayMemmap
from tests import random_docs

rand_array = np.random.random([10, 3])


def da_and_dam():
    rand_docs = random_docs(100)
    da = DocumentArray()
    da.extend(rand_docs)
    rand_docs = random_docs(100)
    dam = DocumentArrayMemmap()
    dam.extend(rand_docs)
    return da, dam


@pytest.mark.skip
@pytest.mark.parametrize(
    'array',
    [
        rand_array,
        torch.Tensor(rand_array),
        tf.constant(rand_array),
        csr_matrix(rand_array),
    ],
)
def test_set_embeddings_multi_kind(array):
    da = DocumentArray([Document() for _ in range(10)])
    da.embeddings = array


@pytest.mark.parametrize('da', da_and_dam())
def test_da_get_embeddings(da):
    np.testing.assert_almost_equal(da.get_attributes('embedding'), da.embeddings)


@pytest.mark.parametrize('da', da_and_dam())
def test_embeddings_setter_da(da):
    emb = np.random.random((100, 128))
    da.embeddings = emb
    np.testing.assert_almost_equal(da.embeddings, emb)

    for x, doc in zip(emb, da):
        np.testing.assert_almost_equal(x, doc.embedding)

    da.embeddings = None
    if hasattr(da, 'flush'):
        da.flush()
    assert not da.embeddings


@pytest.mark.parametrize('da', da_and_dam())
def test_embeddings_wrong_len(da):
    embeddings = np.ones((2, 10))

    with pytest.raises(ValueError):
        da.embeddings = embeddings


@pytest.mark.parametrize('da', da_and_dam())
def test_blobs_getter_da(da):
    blobs = np.random.random((100, 10, 10))
    da.blobs = blobs
    assert len(da) == 100
    np.testing.assert_almost_equal(da.get_attributes('blob'), da.blobs)
    np.testing.assert_almost_equal(da.blobs, blobs)

    da.blobs = None
    if hasattr(da, 'flush'):
        da.flush()
    assert not da.blobs


@pytest.mark.parametrize('da', da_and_dam())
def test_texts_getter_da(da):
    assert len(da.texts) == 100
    assert da.texts == da.get_attributes('text')
    texts = ['text' for _ in range(100)]
    da.texts = texts
    assert da.texts == texts

    for x, doc in zip(texts, da):
        assert x == doc.text

    da.texts = None
    if hasattr(da, 'flush'):
        da.flush()

    # unfortunately protobuf does not distinguish None and '' on string
    # so non-set str field in Pb is ''
    assert da.texts == [''] * 100


@pytest.mark.parametrize('da', da_and_dam())
def test_texts_wrong_len(da):
    texts = ['hello']

    with pytest.raises(ValueError):
        da.texts = texts


@pytest.mark.parametrize('da', da_and_dam())
def test_blobs_wrong_len(da):
    blobs = np.ones((2, 10, 10))

    with pytest.raises(ValueError):
        da.blobs = blobs


@pytest.mark.parametrize('da', da_and_dam())
def test_buffers_getter_setter(da):
    with pytest.raises(ValueError):
        da.buffers = [b'cc', b'bb', b'aa', b'dd']

    da.buffers = [b'aa'] * len(da)
    assert da.buffers == [b'aa'] * len(da)

    da.buffers = None
    if hasattr(da, 'flush'):
        da.flush()

    # unfortunately protobuf does not distinguish None and '' on string
    # so non-set str field in Pb is ''
    assert da.buffers == [b''] * 100
