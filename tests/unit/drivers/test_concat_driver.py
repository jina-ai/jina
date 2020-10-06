import os

import numpy as np

from jina.drivers.helper import array2pb, pb2array
from jina.flow import Flow
from jina.proto import uid
from jina.proto.jina_pb2 import Document

cur_dir = os.path.dirname(os.path.abspath(__file__))

e1 = np.random.random([7])
e2 = np.random.random([5])
e3 = np.random.random([3])
e4 = np.random.random([9])


def input_fn():
    doc1 = Document()
    doc1.embedding.CopyFrom(array2pb(e1))
    c = doc1.chunks.add()
    c.embedding.CopyFrom(array2pb(e2))
    c.id = uid.new_doc_id(c)
    doc2 = Document()
    doc2.embedding.CopyFrom(array2pb(e3))
    d = doc2.chunks.add()
    d.id = uid.new_doc_id(d)
    d.embedding.CopyFrom(array2pb(e4))
    return [doc1, doc2]


def test_array2pb():
    # i don't understand why is this set?
    # os env should be available to that process-context only
    if 'JINA_ARRAY_QUANT' in os.environ:
        print(f'quant is on: {os.environ["JINA_ARRAY_QUANT"]}')
        del os.environ['JINA_ARRAY_QUANT']

    np.testing.assert_almost_equal(pb2array(array2pb(e4)), e4)


def test_concat_embed_driver():
    if 'JINA_ARRAY_QUANT' in os.environ:
        print(f'quant is on: {os.environ["JINA_ARRAY_QUANT"]}')
        del os.environ['JINA_ARRAY_QUANT']

    def validate(req):
        assert len(req.docs) == 2
        assert req.docs[0].embedding.shape == [e1.shape[0] * 2]
        assert req.docs[1].embedding.shape == [e3.shape[0] * 2]
        assert req.docs[0].chunks[0].embedding.shape == [e2.shape[0] * 2]
        assert req.docs[1].chunks[0].embedding.shape == [e4.shape[0] * 2]
        np.testing.assert_almost_equal(pb2array(req.docs[0].embedding), np.concatenate([e1, e1], axis=0), decimal=4)
        np.testing.assert_almost_equal(pb2array(req.docs[0].chunks[0].embedding), np.concatenate([e2, e2], axis=0),
                                       decimal=4)

    # simulate two encoders
    flow = (Flow().add(name='a')
            .add(name='b', needs='gateway')
            .join(needs=['a', 'b'], uses='- !ConcatEmbedDriver | {traversal_paths: [c, r]}'))

    with flow:
        flow.index(input_fn=input_fn, output_fn=validate, callback_on_body=True)
