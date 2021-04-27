import pytest

import numpy as np

from jina.executors.crafters import BaseCrafter
from jina.executors.decorators import (
    batching,
    single,
)
from jina import Document
from jina.flow import Flow
from jina.types.ndarray.generic import NdArray
from jina.types.arrays import DocumentArray
from tests import validate_callback


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


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize(
    'crafter', [DummyCrafterTextSingle(), DummyCrafterTextBatching()]
)
def test_batching_text_one_argument(stack, crafter):
    docs = DocumentArray([Document(text=f'text-{i}') for i in range(15)])
    texts, _ = docs.extract_docs('text', stack_contents=stack)

    crafted_docs = crafter.craft(texts)
    for i, crafted_doc in enumerate(crafted_docs):
        assert crafted_doc['text'] == f'text-{i}-crafted'


@pytest.mark.parametrize(
    'crafter', ['!DummyCrafterTextSingle', '!DummyCrafterTextBatching']
)
def test_batching_text_one_argument_flow(crafter, mocker):
    NUM_DOCS = 15

    def validate_response(resp):
        assert len(resp.index.docs) == NUM_DOCS
        for i, doc in enumerate(resp.index.docs):
            assert doc.text == f'text-{i}-crafted'

    docs = DocumentArray([Document(text=f'text-{i}') for i in range(NUM_DOCS)])
    mock = mocker.Mock()

    with Flow().add(name='crafter', uses=crafter) as f:
        f.index(inputs=docs, on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate_response)


class DummyCrafterTextIdBatching(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @batching(batch_size=3, slice_nargs=2)
    def craft(self, text, id, *args, **kwargs):
        assert len(text) == 3
        assert len(id) == 3
        return [
            {'text': f'{txt}-crafted', 'id': f'{i}-crafted'} for i, txt in zip(id, text)
        ]


class DummyCrafterTextIdSingle(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @single(slice_nargs=2)
    def craft(self, text, id, *args, **kwargs):
        assert isinstance(text, str)
        assert isinstance(id, str)
        return {'text': f'{text}-crafted', 'id': f'{id}-crafted'}


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize(
    'crafter', [DummyCrafterTextIdSingle(), DummyCrafterTextIdBatching()]
)
def test_batching_text_multi(stack, crafter):
    docs = DocumentArray([Document(text=f'text-{i}', id=f'id-{i}') for i in range(15)])
    required_keys = ['text', 'id']
    text_ids, _ = docs.extract_docs(*required_keys, stack_contents=stack)

    crafted_docs = crafter.craft(*text_ids)

    for i, crafted_doc in enumerate(crafted_docs):
        assert crafted_doc['text'] == f'text-{i}-crafted'
        assert crafted_doc['id'] == f'id-{i}-crafted'


@pytest.mark.parametrize(
    'crafter', ['!DummyCrafterTextIdSingle', '!DummyCrafterTextIdBatching']
)
def test_batching_text_multi_flow(crafter, mocker):
    NUM_DOCS = 15

    def validate_response(resp):
        assert len(resp.index.docs) == NUM_DOCS
        for i, doc in enumerate(resp.index.docs):
            assert doc.text == f'text-{i}-crafted'
            assert doc.id == f'id-{i}-crafted'

    docs = DocumentArray(
        [Document(text=f'text-{i}', id=f'id-{i}') for i in range(NUM_DOCS)]
    )
    mock = mocker.Mock()

    with Flow().add(name='crafter', uses=crafter) as f:
        f.index(inputs=docs, on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate_response)


class DummyCrafterBlobBatching(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @batching(batch_size=3)
    def craft(self, blob, *args, **kwargs):
        assert len(blob) == 3
        return [{'blob': b} for b in blob]


class DummyCrafterBlobSingle(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @single
    def craft(self, blob, *args, **kwargs):
        assert isinstance(blob, np.ndarray)
        return {'blob': blob}


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize(
    'crafter', [DummyCrafterBlobSingle(), DummyCrafterBlobBatching()]
)
def test_batching_blob_one_argument(stack, crafter):
    docs = DocumentArray(
        [Document(blob=np.array([[i] * 5, [i] * 5])) for i in range(15)]
    )
    texts, _ = docs.extract_docs('blob', stack_contents=stack)

    crafted_docs = crafter.craft(texts)
    for i, crafted_doc in enumerate(crafted_docs):
        np.testing.assert_equal(crafted_doc['blob'], np.array([[i] * 5, [i] * 5]))


@pytest.mark.parametrize(
    'crafter', ['!DummyCrafterBlobSingle', '!DummyCrafterBlobBatching']
)
def test_batching_blob_one_argument_flow(crafter, mocker):
    NUM_DOCS = 15

    def validate_response(resp):
        assert len(resp.index.docs) == NUM_DOCS
        for i, doc in enumerate(resp.index.docs):
            np.testing.assert_equal(
                NdArray(doc.blob).value, np.array([[i] * 5, [i] * 5])
            )

    docs = DocumentArray(
        [Document(blob=np.array([[i] * 5, [i] * 5])) for i in range(NUM_DOCS)]
    )
    mock = mocker.Mock()

    with Flow().add(name='crafter', uses=crafter) as f:
        f.index(inputs=docs, on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate_response)


class DummyCrafterBlobEmbeddingBatching(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @batching(batch_size=3, slice_nargs=2)
    def craft(self, blob, embedding, *args, **kwargs):
        assert len(blob) == 3
        assert len(embedding) == 3
        return [{'blob': b, 'embedding': e} for b, e in zip(blob, embedding)]


class DummyCrafterBlobEmbeddingSingle(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @single(slice_nargs=2)
    def craft(self, blob, embedding, *args, **kwargs):
        assert isinstance(blob, np.ndarray)
        assert isinstance(embedding, np.ndarray)
        return {'blob': blob, 'embedding': embedding}


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize(
    'crafter', [DummyCrafterBlobEmbeddingSingle(), DummyCrafterBlobEmbeddingBatching()]
)
def test_batching_blob_multi(stack, crafter):
    docs = DocumentArray(
        [
            Document(
                blob=np.array([[i] * 5, [i] * 5]),
                embedding=np.array([i] * 5),
            )
            for i in range(15)
        ]
    )
    required_keys = ['blob', 'embedding']
    text_ids, _ = docs.extract_docs(*required_keys, stack_contents=stack)

    crafted_docs = crafter.craft(*text_ids)

    for i, crafted_doc in enumerate(crafted_docs):
        np.testing.assert_equal(crafted_doc['blob'], np.array([[i] * 5, [i] * 5]))
        np.testing.assert_equal(crafted_doc['embedding'], np.array([i] * 5))


@pytest.mark.parametrize(
    'crafter',
    ['!DummyCrafterBlobEmbeddingSingle', '!DummyCrafterBlobEmbeddingBatching'],
)
def test_batching_blob_multi_flow(crafter, mocker):
    NUM_DOCS = 15

    def validate_response(resp):
        assert len(resp.index.docs) == NUM_DOCS
        for i, doc in enumerate(resp.index.docs):
            np.testing.assert_equal(
                NdArray(doc.blob).value, np.array([[i] * 5, [i] * 5])
            )
            np.testing.assert_equal(NdArray(doc.embedding).value, np.array([i] * 5))

    docs = DocumentArray(
        [
            Document(
                blob=np.array([[i] * 5, [i] * 5]),
                embedding=np.array([i] * 5),
            )
            for i in range(NUM_DOCS)
        ]
    )
    mock = mocker.Mock()

    with Flow().add(name='crafter', uses=crafter) as f:
        f.index(inputs=docs, on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate_response)


class DummyCrafterTextEmbeddingBatching(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @batching(batch_size=3, slice_nargs=2)
    def craft(self, text, embedding, *args, **kwargs):
        assert len(text) == 3
        assert len(embedding) == 3
        return [
            {'text': f'{t}-crafted', 'embedding': e} for t, e in zip(text, embedding)
        ]


class DummyCrafterTextEmbeddingSingle(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_keys = ['text', 'embedding']

    @single(slice_nargs=2)
    def craft(self, text, embedding, *args, **kwargs):
        assert isinstance(text, str)
        assert isinstance(embedding, np.ndarray)
        return {'text': f'{text}-crafted', 'embedding': embedding}


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize(
    'crafter', [DummyCrafterTextEmbeddingSingle(), DummyCrafterTextEmbeddingBatching()]
)
def test_batching_mix_multi(stack, crafter):
    docs = DocumentArray(
        [Document(text=f'text-{i}', embedding=np.array([i] * 5)) for i in range(15)]
    )
    required_keys = ['text', 'embedding']
    text_ids, _ = docs.extract_docs(*required_keys, stack_contents=stack)

    crafted_docs = crafter.craft(*text_ids)

    for i, crafted_doc in enumerate(crafted_docs):
        assert crafted_doc['text'] == f'text-{i}-crafted'
        np.testing.assert_equal(crafted_doc['embedding'], np.array([i] * 5))


@pytest.mark.parametrize(
    'crafter',
    ['!DummyCrafterTextEmbeddingSingle', '!DummyCrafterTextEmbeddingBatching'],
)
def test_batching_mix_multi_flow(crafter, mocker):
    NUM_DOCS = 15

    def validate_response(resp):
        assert len(resp.index.docs) == NUM_DOCS
        for i, doc in enumerate(resp.index.docs):
            assert doc.text == f'text-{i}-crafted'
            np.testing.assert_equal(NdArray(doc.embedding).value, np.array([i] * 5))

    docs = DocumentArray(
        [
            Document(
                text=f'text-{i}',
                embedding=np.array([i] * 5),
            )
            for i in range(NUM_DOCS)
        ]
    )
    mock = mocker.Mock()

    with Flow().add(name='crafter', uses=crafter) as f:
        f.index(inputs=docs, on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate_response)
