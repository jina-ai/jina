import pytest
import numpy as np

from jina.proto import uid
from jina.flow import Flow
from jina.proto.jina_pb2 import Document
from jina.drivers.helper import pb2array, array2pb
from jina.drivers.multimodal import MultimodalDriver

e1 = np.random.random([7])
e2 = np.random.random([5])
e3 = np.random.random([3])
e4 = np.random.random([9])

@pytest.fixture(scope='function')
def embedding():
    class EmbeddingFactory(object):
        def create(self, dim, seed):
            np.random.seed(seed)
            return np.random.random([dim])
    return EmbeddingFactory()


@pytest.fixture(scope='function')
def doc_with_multimodal_chunks(embedding):
    doc = Document()
    chunk1 = doc.chunks.add()
    chunk2 = doc.chunks.add()
    chunk3 = doc.chunks.add()
    chunk1.modality = 'visual'
    chunk2.modality = 'visual'
    chunk3.modality = 'textual'
    chunk1.id = uid.new_doc_id(chunk1)
    chunk2.id = uid.new_doc_id(chunk2)
    chunk3.id = uid.new_doc_id(chunk3)
    # visual features has the same embedding dim.
    chunk1.embedding.CopyFrom(array2pb(embedding.create(dim=16, seed=1)))
    chunk2.embedding.CopyFrom(array2pb(embedding.create(dim=16, seed=2)))
    chunk3.embedding.CopyFrom(array2pb(embedding.create(dim=24, seed=3)))
    return doc

@pytest.fixture(scope='function')
def flow():
    return (Flow().add(name='a')
         .add(name='b', needs='gateway')
         .join(needs=['a', 'b'], uses='- !MultimodalDriver | {}'))

def test_multimodal_driver(doc_with_multimodal_chunks, flow, embedding):
    def input_fn():
        return [doc_with_multimodal_chunks]

    def validate(req):
        doc = req.docs[0]
        embedding1 = embedding.create(dim=16, seed=1)
        embedding2 = embedding.create(dim=16, seed=2)
        embedding3 = embedding.create(dim=24, seed=3)
        chunk1 = doc.chunks[0]
        chunk2 = doc.chunks[1]
        chunk3 = doc.chunks[2]

        assert len(req.docs) == 1
        assert len(doc.chunks) == 3
        assert chunk1.embedding.shape == [embedding1.shape[0]]
        assert chunk2.embedding.shape == [embedding2.shape[0]]
        assert chunk3.embedding.shape == [embedding3.shape[0]]
        # TODO add np testing after resolve question.

    with flow:
        flow.index(input_fn=input_fn, output_fn=validate, callback_on_body=True)