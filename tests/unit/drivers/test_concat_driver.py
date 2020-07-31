import numpy as np

from jina.drivers.helper import array2pb, pb2array
from jina.flow import Flow
from jina.proto.jina_pb2 import Document
from tests import JinaTestCase


def input_fn():
    doc1 = Document()
    doc1.id = 1
    doc1.embedding.CopyFrom(array2pb(np.random.random([7])))
    c = doc1.chunks.add()
    c.id = 3
    c.embedding.CopyFrom(array2pb(np.random.random([5])))
    doc2 = Document()
    doc2.id = 2
    doc2.embedding.CopyFrom(array2pb(np.random.random([3])))
    d = doc2.chunks.add()
    d.id = 4
    d.embedding.CopyFrom(array2pb(np.random.random([9])))
    return [doc1, doc2]


class ConcatDriverTestCase(JinaTestCase):

    def test_direct_concat(self):
        doc1, doc2 = input_fn()
        t1 = np.concatenate([pb2array(doc1.embedding), pb2array(doc2.embedding)], axis=0)
        doc1.embedding.buffer += doc2.embedding.buffer
        doc1.embedding.shape[0] += doc2.embedding.shape[0]
        t2 = pb2array(doc1.embedding)
        self.assertEqual(t1.shape[0], 10)
        self.assertEqual(t2.shape[0], 10)
        np.testing.assert_almost_equal(t1, t2)

    def test_concat_embed_driver(self):
        def validate(req):
            self.assertEqual(len(req.docs), 2)
            self.assertEqual(req.docs[0].embedding.shape, [14])
            self.assertEqual(req.docs[1].embedding.shape, [6])
            self.assertEqual(req.docs[0].chunks[0].embedding.shape, [10])
            self.assertEqual(req.docs[1].chunks[0].embedding.shape, [18])

        # simulate two encoders
        flow = (Flow().add(name='a')
                .add(name='b', needs='gateway')
                .join(needs=['a', 'b'], uses='- !ConcatEmbedDriver | {depth_range: [0, 1]}'))

        with flow:
            flow.index(input_fn=input_fn, output_fn=validate, callback_on_body=True)
