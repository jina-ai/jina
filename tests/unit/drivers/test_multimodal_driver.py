import pytest
import numpy as np

from jina.proto import uid
from jina.flow import Flow
from jina.proto.jina_pb2 import Document
from jina.drivers.helper import pb2array, array2pb


@pytest.fixture(scope='function')
def embedding():
    class EmbeddingFactory(object):
        def create(self, dim, seed):
            np.random.seed(seed)
            return np.random.random([dim])
    return EmbeddingFactory()

@pytest.fixture(scope='function')
def embeddings(embedding):
    return [
        embedding.create(dim=16, seed=1),
        embedding.create(dim=16, seed=2),
        embedding.create(dim=24, seed=3)
    ]

@pytest.fixture(scope='function')
def doc_with_multimodal_chunks(embeddings):
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
    chunk1.embedding.CopyFrom(array2pb(embeddings[0]))
    chunk2.embedding.CopyFrom(array2pb(embeddings[1]))
    chunk3.embedding.CopyFrom(array2pb(embeddings[2]))
    return doc

@pytest.fixture(scope='function')
def flow():
    return (Flow().add(name='a')
         .add(name='b', needs='gateway')
         .join(needs=['a', 'b'], uses='- !MultimodalDriver | {}'))

def test_multimodal_driver(flow, embeddings, doc_with_multimodal_chunks):
    def input_fn():
        return [doc_with_multimodal_chunks]

    def validate(req):
        doc = req.docs[0]
        chunk1 = doc.chunks[0]
        chunk2 = doc.chunks[1]
        chunk3 = doc.chunks[2]

        assert len(req.docs) == 1
        assert len(doc.chunks) == 3
        assert chunk1.embedding.shape == [embeddings[0].shape[0]]
        assert chunk2.embedding.shape == [embeddings[1].shape[0]]
        assert chunk3.embedding.shape == [embeddings[2].shape[0]]
        assert chunk1.modality == chunk2.modality == 'visual'
        assert chunk3.modality == 'textual'
        # TODO add np testing after resolve question.

    with flow:
        flow.index(input_fn=input_fn, output_fn=validate, callback_on_body=True)