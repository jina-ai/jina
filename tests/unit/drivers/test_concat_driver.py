import os

import numpy as np

from jina import Document
from jina.flow import Flow
from jina.types.ndarray.generic import NdArray

from tests import validate_callback

e1 = np.random.random([7])
e2 = np.random.random([5])
e3 = np.random.random([3])
e4 = np.random.random([9])


def input_function():
    with Document() as doc1:
        doc1.embedding = e1
        with Document() as chunk1:
            chunk1.embedding = e2
            chunk1.id = 1
        doc1.chunks.add(chunk1)
    with Document() as doc2:
        doc2.embedding = e3
        with Document() as chunk2:
            chunk2.embedding = e4
            chunk2.id = 2
        doc2.chunks.add(chunk2)
    return [doc1, doc2]


def test_array2pb():
    # i don't understand why is this set?
    # os env should be available to that process-context only
    if 'JINA_ARRAY_QUANT' in os.environ:
        print(f'quant is on: {os.environ["JINA_ARRAY_QUANT"]}')
        del os.environ['JINA_ARRAY_QUANT']

    d = NdArray()
    d.value = e4
    np.testing.assert_almost_equal(d.value, e4)


def test_concat_embed_driver(mocker):
    if 'JINA_ARRAY_QUANT' in os.environ:
        print(f'quant is on: {os.environ["JINA_ARRAY_QUANT"]}')
        del os.environ['JINA_ARRAY_QUANT']

    def validate(req):
        assert len(req.docs) == 2
        assert NdArray(req.docs[0].embedding).value.shape == (e1.shape[0] * 2,)
        assert NdArray(req.docs[1].embedding).value.shape == (e3.shape[0] * 2,)
        np.testing.assert_almost_equal(
            NdArray(req.docs[0].embedding).value,
            np.concatenate([e1, e1], axis=0),
            decimal=4,
        )

    mock = mocker.Mock()
    # simulate two encoders
    flow = (
        Flow()
        .add(name='a')
        .add(name='b', needs='gateway')
        .join(needs=['a', 'b'], uses='- !ConcatEmbedDriver | {}')
    )

    with flow:
        flow.index(inputs=input_function, on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate)
