import pytest

from jina.executors.segmenters import BaseSegmenter
from jina.executors.decorators import batching, single
from jina import Document
from jina.types.sets import DocumentSet


class DummySegmenterTextBatching(BaseSegmenter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0

    @batching(batch_size=3)
    def segment(self, text, *args, **kwargs):
        assert len(text) == 3
        num_chunks = 3
        return [
            [{'text': f'{txt}-chunk-{chunk}'} for chunk in range(num_chunks)]
            for txt in text
        ]


class DummySegmenterTextSingle(BaseSegmenter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @single(flatten_output=False)
    def segment(self, text, *args, **kwargs):
        assert isinstance(text, str)
        num_chunks = 3
        return [{'text': f'{text}-chunk-{chunk}'} for chunk in range(num_chunks)]


@pytest.mark.parametrize(
    'segmenter', [DummySegmenterTextSingle(), DummySegmenterTextBatching()]
)
def test_batching_text_one_argument(segmenter):
    docs = DocumentSet([Document(text=f'text-{i}') for i in range(15)])
    texts, _ = docs.extract_docs('text')

    chunks_sets = segmenter.segment(texts)
    for i, chunks in enumerate(chunks_sets):
        assert len(chunks) == 3
        for j, chunk in enumerate(chunks):
            assert chunk['text'] == f'text-{i}-chunk-{j}'


class DummySegmenterBlobBatching(BaseSegmenter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0

    @batching(batch_size=3)
    def segment(self, text, *args, **kwargs):
        assert len(text) == 3
        num_chunks = 3
        return [
            [{'text': f'{txt}-chunk-{chunk}'} for chunk in range(num_chunks)]
            for txt in text
        ]
