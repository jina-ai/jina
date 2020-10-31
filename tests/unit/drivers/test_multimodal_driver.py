import numpy as np
import pytest

from jina.drivers.multimodal import MultiModalDriver
from jina.executors.encoders.multimodal import BaseMultiModalEncoder
from jina.proto import jina_pb2
from jina.proto import uid
from jina.proto.ndarray.generic import GenericNdArray


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
    GenericNdArray(chunk1.embedding).value = embeddings[0]
    GenericNdArray(chunk2.embedding).value = embeddings[1]
    GenericNdArray(chunk3.embedding).value = embeddings[2]
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
    assert GenericNdArray(doc.embedding).value.shape[0] == GenericNdArray(visual1.embedding).value.shape[0] + \
           GenericNdArray(visual2.embedding).value.shape[0] + GenericNdArray(textual.embedding).value.shape[0]


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
    GenericNdArray(chunk1.embedding).value = embeddings[0]
    GenericNdArray(chunk2.embedding).value = embeddings[1]
    GenericNdArray(chunk3.embedding).value = embeddings[2]
    return doc


def test_multimodal_driver_assert_one_chunk_per_modality(simple_multimodal_driver, mock_multimodal_encoder,
                                                         doc_with_multimodal_chunks_wrong):
    simple_multimodal_driver.attach(executor=mock_multimodal_encoder, pea=None)
    simple_multimodal_driver._apply_all([doc_with_multimodal_chunks_wrong])
    doc = doc_with_multimodal_chunks_wrong
    assert len(doc.chunks) == 3
    # Document consider invalid to be encoded by the driver
    assert GenericNdArray(doc.embedding).value is None


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
    control = np.concatenate([GenericNdArray(visual2.embedding).value, GenericNdArray(textual.embedding).value,
                              GenericNdArray(visual1.embedding).value])
    test = GenericNdArray(doc.embedding).value
    np.testing.assert_array_equal(control, test)
