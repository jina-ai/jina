import pytest
from collections import OrderedDict
from jina import Document, DocumentArray, Executor, Flow, requests
from jina.types.document.multimodal import MultimodalDocument
from jina.types.arrays.chunk import ChunkArray


class DummyExecutor(Executor):
    def __init__(self, mode=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if mode:
            self._mode = str(mode)

    @requests
    def do_something(self, docs, **kwargs):
        for doc in docs:
            chunks = ChunkArray(
                (d for d in doc.chunks if d.modality == self._mode), doc
            )
            assert chunks[0].content == self._mode
            assert len(chunks) == 1
            doc.chunks = chunks


class MatchMerger(Executor):
    @requests
    def merge(self, docs_matrix, **kwargs):
        results = OrderedDict()
        for docs in docs_matrix:
            for doc in docs:
                if doc.id in results:
                    results[doc.id].matches.extend(doc.matches)
                else:
                    results[doc.id] = doc
        return DocumentArray(results.values())


class ChunkMerger(Executor):
    @requests
    def merge(self, docs_matrix, **kwargs):
        results = OrderedDict()
        for docs in docs_matrix:
            for doc in docs:
                if doc.id in results:
                    results[doc.id].chunks.extend(doc.chunks)
                else:
                    results[doc.id] = doc
        return DocumentArray(results.values())


@pytest.mark.timeout(5)
@pytest.mark.parametrize('num_replicas, num_shards', [(1, 1), (2, 2)])
def test_sharding_tail_pea(num_replicas, num_shards):
    """TODO(Maximilian): Make (1, 2) and (2, 1) also workable"""

    f = Flow().add(
        uses=DummyExecutor,
        replicas=num_replicas,
        shards=num_shards,
        uses_after=MatchMerger,
    )
    with f:
        results = f.post(
            on='/search',
            inputs=Document(matches=[Document()]),
            return_results=True,
        )
        assert len(results[0].docs[0].matches) == num_shards


def test_merging_head_pea():
    def multimodal_generator():
        for i in range(0, 5):
            document = MultimodalDocument(modality_content_map={'1': '1', '2': '2'})
            yield document

    f = (
        Flow()
        .add(uses={'jtype': 'DummyExecutor', 'with': {'mode': '1'}}, name='pod1')
        .add(
            uses={'jtype': 'DummyExecutor', 'with': {'mode': '2'}},
            name='pod2',
            needs='gateway',
        )
        .add(uses_before=ChunkMerger, name='pod3', needs=['pod1', 'pod2'])
    )
    with f:
        results = f.post(
            on='/search',
            inputs=multimodal_generator(),
            return_results=True,
        )
        assert len(results[0].docs[0].chunks) == 2
        assert len(results[0].docs) == 5
