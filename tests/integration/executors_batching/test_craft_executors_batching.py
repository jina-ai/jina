import pytest

import numpy as np

from jina.executors.crafters import BaseCrafter
from jina.executors.decorators import batching, batching_multi_input, single, single_multi_input
from jina import Document
from jina.types.sets import DocumentSet


class DummyCrafterTextBatching(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @batching(batch_size=3)
    def craft(self, text, *args, **kwargs):
        assert len(text) == 3
        return [{'text': f'{txt}-crafted'} for txt in text]


class DummyCrafterTextSingle(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @single
    def craft(self, text, *args, **kwargs):
        assert isinstance(text, str)
        return {'text': f'{text}-crafted'}


@pytest.mark.parametrize('crafter', [DummyCrafterTextSingle(), DummyCrafterTextBatching()])
def test_batching_text_one_argument(crafter):
    docs = DocumentSet([Document(text=f'text-{i}') for i in range(15)])
    texts, _ = docs._extract_docs('text')

    crafted_docs = crafter.craft(texts)
    for i, crafted_doc in enumerate(crafted_docs):
        assert crafted_doc['text'] == f'text-{i}-crafted'


class DummyCrafterTextIdBatching(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @batching_multi_input(batch_size=3, num_data=2)
    def craft(self, text, id, *args, **kwargs):
        assert len(text) == 3
        assert len(id) == 3
        return [{'text': f'{txt}-crafted', 'id': f'{i}-crafted'} for i, txt in zip(id, text)]


class DummyCrafterTextIdSingle(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @single_multi_input(num_data=2)
    def craft(self, text, id, *args, **kwargs):
        assert isinstance(text, str)
        assert isinstance(id, str)
        return {'text': f'{text}-crafted', 'id': f'{id}-crafted'}


@pytest.mark.parametrize('crafter', [DummyCrafterTextIdSingle(), DummyCrafterTextIdBatching()])
def test_batching_text_multi(crafter):
    docs = DocumentSet([Document(text=f'text-{i}', id=f'id-{i}') for i in range(15)])
    required_keys = ['text', 'id']
    text_ids, _ = docs._extract_docs(*required_keys)

    args = [text_ids[:, i] for i in range(len(required_keys))]
    crafted_docs = crafter.craft(*args)

    for i, crafted_doc in enumerate(crafted_docs):
        assert crafted_doc['text'] == f'text-{i}-crafted'
        assert crafted_doc['id'] == f'id-{i}-crafted'


class DummyCrafterBlobBatching(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @batching(batch_size=3)
    def craft(self, blob, *args, **kwargs):
        assert len(blob) == 3
        assert blob.shape == (3, 2, 5)
        return [{'blob': b} for b in blob]


class DummyCrafterBlobSingle(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @single
    def craft(self, blob, *args, **kwargs):
        assert isinstance(blob, np.ndarray)
        return {'blob': blob}


@pytest.mark.parametrize('crafter', [DummyCrafterBlobSingle(), DummyCrafterBlobBatching()])
def test_batching_blob_one_argument(crafter):
    docs = DocumentSet([Document(blob=np.array([[i, i, i, i, i], [i, i, i, i, i]])) for i in range(15)])
    texts, _ = docs._extract_docs('blob')

    crafted_docs = crafter.craft(texts)
    for i, crafted_doc in enumerate(crafted_docs):
        np.testing.assert_equal(crafted_doc['blob'], np.array([[i, i, i, i, i], [i, i, i, i, i]]))


class DummyCrafterBlobEmbeddingBatching(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @batching_multi_input(batch_size=3, num_data=2)
    def craft(self, blob, embedding, *args, **kwargs):
        print(f' blob {blob}')
        assert len(blob) == 3
        assert len(embedding) == 3
        assert blob.shape == (3, 2, 5)
        assert embedding.shape == (3, 1, 5)
        return [{'blob': b, 'embedding': e} for b, e in zip(blob, embedding)]


class DummyCrafterBlobEmbeddingSingle(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @single_multi_input(num_data=2)
    def craft(self, blob, embedding, *args, **kwargs):
        assert isinstance(blob, np.ndarray)
        assert isinstance(embedding, np.ndarray)
        return {'blob': blob, 'embedding': embedding}


@pytest.mark.parametrize('crafter', [DummyCrafterBlobEmbeddingSingle(), DummyCrafterBlobEmbeddingBatching()])
def test_batching_blob_multi(crafter):
    docs = DocumentSet([Document(blob=np.array([[i, i, i, i, i], [i, i, i, i, i]]), embedding=np.array([i, i, i, i, i])) for i in range(15)])
    required_keys = ['blob', 'embedding']
    text_ids, _ = docs._extract_docs(*required_keys)

    args = [text_ids[:, i] for i in range(len(required_keys))]
    crafted_docs = crafter.craft(*args)

    for i, crafted_doc in enumerate(crafted_docs):
        np.testing.assert_equal(crafted_doc['blob'], np.array([[i, i, i, i, i], [i, i, i, i, i]]))
        np.testing.assert_equal(crafted_doc['embedding'], np.array([i, i, i, i, i]))
