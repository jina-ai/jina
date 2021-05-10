import pytest

import numpy as np

from jina.executors.encoders import BaseEncoder
from jina.executors.decorators import batching, single, as_ndarray
from jina import Document
from jina.types.arrays import DocumentArray

EMBED_SIZE = 10


class DummyEncoderTextBatching(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @as_ndarray
    @batching(batch_size=3)
    def encode(self, content: 'np.ndarray', *args, **kwargs):
        assert isinstance(content, np.ndarray)
        assert isinstance(content[0], str)
        assert content.shape[0] == 3
        return np.random.random((content.shape[0], EMBED_SIZE))


class DummyEncoderTextSingle(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @as_ndarray
    @single
    def encode(self, content, *args, **kwargs):
        assert isinstance(content, str)
        return np.random.random(EMBED_SIZE)


@pytest.mark.parametrize(
    'encoder', [DummyEncoderTextSingle(), DummyEncoderTextBatching()]
)
def test_batching_encode_text(encoder):
    docs = DocumentArray([Document(text=f'text-{i}') for i in range(15)])
    texts, _ = docs.all_contents

    embeds = encoder.encode(texts)

    assert embeds.shape == (15, 10)


class DummyEncoderBlobBatching(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @as_ndarray
    @batching(batch_size=3)
    def encode(self, content, *args, **kwargs):
        assert isinstance(content, np.ndarray)
        assert isinstance(content[0], np.ndarray)
        assert content.shape[0] == 3
        return np.random.random((content.shape[0], EMBED_SIZE))


class DummyEncoderBlobSingle(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @as_ndarray
    @single
    def encode(self, content, *args, **kwargs):
        assert isinstance(content, np.ndarray)
        return np.random.random(EMBED_SIZE)


@pytest.mark.parametrize(
    'encoder', [DummyEncoderBlobSingle(), DummyEncoderBlobBatching()]
)
def test_batching_encode_blob(encoder):
    docs = DocumentArray([Document(blob=np.random.random((10, 20))) for _ in range(15)])
    blob, _ = docs.all_contents

    embeds = encoder.encode(blob)

    assert embeds.shape == (15, 10)
