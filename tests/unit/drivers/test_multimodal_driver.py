import pytest
import numpy as np

from jina.proto import uid
from jina.proto import jina_pb2
from jina.drivers.helper import array2pb
from jina.executors.encoders.multimodal import BaseMultiModalEncoder
from jina.drivers.multimodal import MultimodalDriver


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
    doc = jina_pb2.Document()
    chunk1 = doc.chunks.add()
    chunk2 = doc.chunks.add()
    chunk3 = doc.chunks.add()
    chunk1.modality = 'visual1'
    chunk2.modality = 'visual2'
    chunk3.modality = 'textual'
    chunk1.id = uid.new_doc_id(chunk1)
    chunk2.id = uid.new_doc_id(chunk2)
    chunk3.id = uid.new_doc_id(chunk3)
    chunk1.embedding.CopyFrom(array2pb(embeddings[0]))
    chunk2.embedding.CopyFrom(array2pb(embeddings[1]))
    chunk3.embedding.CopyFrom(array2pb(embeddings[2]))
    return doc


class MockMultiModalEncoder(BaseMultiModalEncoder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.position_by_modality = {'visual1': 0,
                                     'visual2': 1,
                                     'textual': 2}

    def encode(self, *data: 'np.ndarray', **kwargs) -> 'np.ndarray':
        visual1 = data[self.position_by_modality['visual1']]
        visual2 = data[self.position_by_modality['visual2']]
        textual = data[self.position_by_modality['textual']]
        return np.concatenate((visual1, visual2, textual), axis=1)


@pytest.fixture
def mock_multimodal_encoder():
    return MockMultiModalEncoder()


class SimpleMultiModalDriver(MultimodalDriver):

    def __init__(self, *args, **kwargs):
        import logging
        super().__init__(*args, **kwargs)
        self.test_logger = logging.getLogger('test multimodal driver')

    @property
    def logger(self):
        return self.test_logger

    @property
    def exec_fn(self):
        return self._exec_fn


@pytest.fixture
def simple_multimodal_driver():
    return SimpleMultiModalDriver()


def test_multimodal_driver(simple_multimodal_driver, mock_multimodal_encoder, doc_with_multimodal_chunks):
    simple_multimodal_driver.attach(executor=mock_multimodal_encoder, pea=None)
    simple_multimodal_driver._apply_all([doc_with_multimodal_chunks])
    doc = doc_with_multimodal_chunks
    assert len(doc.chunks) == 3
    visual1 = doc.chunks[0]
    visual2 = doc.chunks[1]
    textual = doc.chunks[2]
    assert doc.embedding.shape[0] == visual1.embedding.shape[0] + visual2.embedding.shape[0] + textual.embedding.shape[
        0]


@pytest.fixture(scope='function')
def doc_with_multimodal_chunks_wrong(embeddings):
    doc = jina_pb2.Document()
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


def test_multimodal_driver_assert_one_chunk_per_modality(simple_multimodal_driver, mock_multimodal_encoder,
                                                         doc_with_multimodal_chunks_wrong):
    simple_multimodal_driver.attach(executor=mock_multimodal_encoder, pea=None)
    simple_multimodal_driver._apply_all([doc_with_multimodal_chunks_wrong])
    doc = doc_with_multimodal_chunks_wrong
    assert len(doc.chunks) == 3
    # Document consider invalid to be encoded by the driver
    assert len(doc.embedding.buffer) == 0
