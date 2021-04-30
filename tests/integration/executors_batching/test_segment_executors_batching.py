import pytest

from jina.executors.segmenters import BaseSegmenter
from jina.executors.decorators import batching, single
from jina import Document
from jina.flow import Flow
from jina.types.arrays import DocumentArray
from tests import validate_callback

NUM_CHUNKS = 3


class DummySegmenterTextBatching(BaseSegmenter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0

    @batching(batch_size=3)
    def segment(self, text, *args, **kwargs):
        assert len(text) == 3
        return [
            [{'text': f'{txt}-chunk-{chunk}'} for chunk in range(NUM_CHUNKS)]
            for txt in text
        ]


class DummySegmenterTextSingle(BaseSegmenter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @single
    def segment(self, text, *args, **kwargs):
        assert isinstance(text, str)
        return [{'text': f'{text}-chunk-{chunk}'} for chunk in range(NUM_CHUNKS)]


@pytest.mark.parametrize(
    'segmenter', [DummySegmenterTextSingle(), DummySegmenterTextBatching()]
)
def test_batching_text_one_argument(segmenter):
    docs = DocumentArray([Document(text=f'text-{i}') for i in range(15)])
    texts, _ = docs.extract_docs('text')

    chunks_sets = segmenter.segment(texts)
    for i, chunks in enumerate(chunks_sets):
        assert len(chunks) == NUM_CHUNKS
        for j, chunk in enumerate(chunks):
            assert chunk['text'] == f'text-{i}-chunk-{j}'


@pytest.mark.parametrize(
    'segmenter', ['!DummySegmenterTextSingle', '!DummySegmenterTextBatching']
)
def test_batching_text_one_argument_flow(segmenter, mocker):
    NUM_DOCS = 15

    def validate_response(resp):
        assert len(resp.index.docs) == NUM_DOCS
        for i, doc in enumerate(resp.index.docs):
            assert len(doc.chunks) == NUM_CHUNKS
            for j, chunk in enumerate(doc.chunks):
                assert chunk.text == f'text-{i}-chunk-{j}'

    docs = DocumentArray([Document(text=f'text-{i}') for i in range(NUM_DOCS)])
    mock = mocker.Mock()

    with Flow().add(name='segmenter', uses=segmenter) as f:
        f.index(inputs=docs, on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate_response)
