import os

import numpy as np

from jina.flow import Flow
from jina.proto import uid
from jina.proto.jina_pb2 import Document
from jina.proto.ndarray.generic import GenericNdArray

cur_dir = os.path.dirname(os.path.abspath(__file__))

e1 = np.random.random([7])
e2 = np.random.random([5])
e3 = np.random.random([3])
e4 = np.random.random([9])


def input_fn():
    doc1 = Document()
    GenericNdArray(doc1.embedding).value = e1
    c = doc1.chunks.add()
    GenericNdArray(c.embedding).value = e2
    c.id = uid.new_doc_id(c)
    doc2 = Document()
    GenericNdArray(doc2.embedding).value = e3
    d = doc2.chunks.add()
    d.id = uid.new_doc_id(d)
    GenericNdArray(d.embedding).value = e4
    return [doc1, doc2]


def test_array2pb():
    # i don't understand why is this set?
    # os env should be available to that process-context only
    if 'JINA_ARRAY_QUANT' in os.environ:
        print(f'quant is on: {os.environ["JINA_ARRAY_QUANT"]}')
        del os.environ['JINA_ARRAY_QUANT']

    d = GenericNdArray()
    d.value = e4
    np.testing.assert_almost_equal(d.value, e4)


def test_concat_embed_driver():
    if 'JINA_ARRAY_QUANT' in os.environ:
        print(f'quant is on: {os.environ["JINA_ARRAY_QUANT"]}')
        del os.environ['JINA_ARRAY_QUANT']

    def validate(req):
        assert len(req.docs) == 2
        assert GenericNdArray(req.docs[0].embedding).value.shape == (e1.shape[0] * 2,)
        assert GenericNdArray(req.docs[1].embedding).value.shape == (e3.shape[0] * 2,)
        # assert GenericNdArray(req.docs[0].chunks[0].embedding).value.shape == (e2.shape[0] * 2,)
        # assert GenericNdArray(req.docs[1].chunks[0].embedding).value.shape == (e4.shape[0] * 2,)
        np.testing.assert_almost_equal(GenericNdArray(req.docs[0].embedding).value, np.concatenate([e1, e1], axis=0),
                                       decimal=4)
        # np.testing.assert_almost_equal(GenericNdArray(req.docs[0].chunks[0].embedding).value,
        #                                np.concatenate([e2, e2], axis=0),
        #                                decimal=4)

    # simulate two encoders
    flow = (Flow().add(name='a')
            .add(name='b', needs='gateway')
            .join(needs=['a', 'b'], uses='- !ConcatEmbedDriver | {}'))

    with flow:
        flow.index(input_fn=input_fn, output_fn=validate, callback_on_body=True)
