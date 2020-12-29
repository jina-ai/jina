import os

import numpy as np

from jina import Document
from jina.flow import Flow
from jina.types.document.uid import UniqueId
from jina.types.ndarray.generic import NdArray

e1 = np.random.random([7])
e2 = np.random.random([5])
e3 = np.random.random([3])
e4 = np.random.random([9])


def input_fn():
    with Document() as doc1:
        doc1.embedding = e1
        with Document() as chunk1:
            chunk1.embedding = e2
            chunk1.id = UniqueId(1)
        doc1.chunks.add(chunk1)
    with Document() as doc2:
        doc2.embedding = e3
        with Document() as chunk2:
            chunk2.embedding = e4
            chunk2.id = UniqueId(2)
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
        mock()
        assert len(req.docs) == 2
        assert NdArray(req.docs[0].embedding).value.shape == (e1.shape[0] * 2,)
        assert NdArray(req.docs[1].embedding).value.shape == (e3.shape[0] * 2,)
        np.testing.assert_almost_equal(NdArray(req.docs[0].embedding).value, np.concatenate([e1, e1], axis=0),
                                       decimal=4)

    mock = mocker.Mock()
    # simulate two encoders
    flow = (Flow().add(name='a')
            .add(name='b', needs='gateway')
            .join(needs=['a', 'b'], uses='- !ConcatEmbedDriver | {}'))

    with flow:
        flow.index(input_fn=input_fn, on_done=validate, callback_on='body')

    mock.assert_called_once()
