import numpy as np
import pytest

from jina.drivers.multimodal import MultiModalDriver
from jina.executors.encoders.multimodal import BaseMultiModalEncoder
from jina import Document


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
    chunk1 = Document()
    chunk2 = Document()
    chunk3 = Document()
    chunk1.modality = 'visual1'
    chunk2.modality = 'visual2'
    chunk3.modality = 'textual'
    chunk1.embedding = embeddings[0]
    chunk2.embedding = embeddings[1]
    chunk3.embedding = embeddings[2]
    chunk1.update_id()
    chunk2.update_id()
    chunk3.update_id()
    doc.update_id()
    doc.add_chunk(chunk1)
    doc.add_chunk(chunk2)
    doc.add_chunk(chunk3)
    return doc


class MockMultiModalEncoder(BaseMultiModalEncoder):

    def __init__(self, positional_modality, *args, **kwargs):
        super().__init__(positional_modality=positional_modality, *args, **kwargs)

    def encode(self, *data: 'np.ndarray', **kwargs) -> 'np.ndarray':
        visual1 = data[(self.positional_modality.index('visual1'))]
        visual2 = data[(self.positional_modality.index('visual2'))]
        textual = data[(self.positional_modality.index('textual'))]
        return np.concatenate((visual1, visual2, textual), axis=1)


@pytest.fixture
def mock_multimodal_encoder():
    return MockMultiModalEncoder(positional_modality=['visual1', 'visual2', 'textual'])


class SimpleMultiModalDriver(MultiModalDriver):

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
    assert doc.embedding.shape[0] == visual1.embedding.shape[0] + \
           visual2.embedding.shape[0] + textual.embedding.shape[0]


@pytest.fixture(scope='function')
def doc_with_multimodal_chunks_wrong(embeddings):
    doc = Document()
    chunk1 = Document()
    chunk2 = Document()
    chunk3 = Document()
    chunk1.modality = 'visual'
    chunk2.modality = 'visual'
    chunk3.modality = 'textual'
    chunk1.embedding = embeddings[0]
    chunk2.embedding = embeddings[1]
    chunk3.embedding = embeddings[2]
    chunk1.update_id()
    chunk2.update_id()
    chunk3.update_id()
    doc.update_id()
    doc.add_chunk(chunk1)
    doc.add_chunk(chunk2)
    doc.add_chunk(chunk3)
    return doc


def test_multimodal_driver_assert_one_chunk_per_modality(simple_multimodal_driver, mock_multimodal_encoder,
                                                         doc_with_multimodal_chunks_wrong):
    simple_multimodal_driver.attach(executor=mock_multimodal_encoder, pea=None)
    simple_multimodal_driver._apply_all([doc_with_multimodal_chunks_wrong])
    doc = doc_with_multimodal_chunks_wrong
    assert len(doc.chunks) == 3
    # DocumentProto consider invalid to be encoded by the driver
    assert doc.embedding is None


@pytest.fixture
def mock_multimodal_encoder_shuffled():
    return MockMultiModalEncoder(positional_modality=['visual2', 'textual', 'visual1'])


def test_multimodal_driver_with_shuffled_order(simple_multimodal_driver, mock_multimodal_encoder_shuffled,
                                               doc_with_multimodal_chunks):
    simple_multimodal_driver.attach(executor=mock_multimodal_encoder_shuffled, pea=None)
    simple_multimodal_driver._apply_all([doc_with_multimodal_chunks])
    doc = doc_with_multimodal_chunks
    assert len(doc.chunks) == 3
    visual1 = doc.chunks[2]
    visual2 = doc.chunks[0]
    textual = doc.chunks[1]
    control = np.concatenate([visual2.embedding, textual.embedding,
                              visual1.embedding])
    test = doc.embedding
    np.testing.assert_array_equal(control, test)
