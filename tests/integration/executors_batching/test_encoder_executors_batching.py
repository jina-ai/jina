import pytest

import numpy as np

from jina.executors.encoders import BaseEncoder
from jina.executors.decorators import batching, single, as_ndarray
from jina import Document
from jina.types.sets import DocumentSet

EMBED_SIZE = 10


class DummyEncoderTextBatching(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @as_ndarray
    @batching(batch_size=3)
    def encode(self, data, *args, **kwargs):
        assert isinstance(data, np.ndarray)
        assert isinstance(data[0], str)
        assert data.shape[0] == 3
        return np.random.random((data.shape[0], EMBED_SIZE))


class DummyEncoderTextSingle(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @as_ndarray
    @single
    def encode(self, data, *args, **kwargs):
        assert isinstance(data, str)
        return np.random.random(EMBED_SIZE)


@pytest.mark.parametrize(
    'encoder', [DummyEncoderTextSingle(), DummyEncoderTextBatching()]
)
def test_batching_encode_text(encoder):
    docs = DocumentSet([Document(text=f'text-{i}') for i in range(15)])
    texts, _ = docs.extract_docs('text')

    embeds = encoder.encode(texts)

    assert embeds.shape == (15, 10)


class DummyEncoderBlobBatching(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @as_ndarray
    @batching(batch_size=3)
    def encode(self, data, *args, **kwargs):
        assert isinstance(data, np.ndarray)
        assert isinstance(data[0], np.ndarray)
        assert data.shape[0] == 3
        return np.random.random((data.shape[0], EMBED_SIZE))


class DummyEncoderBlobSingle(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @as_ndarray
    @single
    def encode(self, data, *args, **kwargs):
        assert isinstance(data, np.ndarray)
        return np.random.random(EMBED_SIZE)


@pytest.mark.parametrize(
    'encoder', [DummyEncoderBlobSingle(), DummyEncoderBlobBatching()]
)
def test_batching_encode_blob(encoder):
    docs = DocumentSet([Document(blob=np.random.random((10, 20))) for _ in range(15)])
    blob, _ = docs.extract_docs('blob')

    embeds = encoder.encode(blob)

    assert embeds.shape == (15, 10)
