from collections import OrderedDict

import pytest
from docarray.array.chunk import ChunkArray

from jina import Client, Document, DocumentArray, Executor, Flow, requests
from jina.helper import random_port


class DummyExecutor(Executor):
    def __init__(self, mode=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if mode:
            self._mode = str(mode)

    @requests
    def do_something(self, docs, **kwargs):
        for doc in docs:
            if len(doc.chunks) > 0:
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
        return DocumentArray(list(results.values()))


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
        return DocumentArray(list(results.values()))


@pytest.mark.timeout(60)
@pytest.mark.parametrize('num_replicas, num_shards', [(1, 1), (2, 2)])
def test_sharding_tail_pod(num_replicas, num_shards):
    """TODO(Maximilian): Make (1, 2) and (2, 1) also workable"""
    port = random_port()
    f = Flow(port=port).add(
        uses=DummyExecutor,
        replicas=num_replicas,
        shards=num_shards,
        uses_after=MatchMerger,
    )
    with f:
        results = Client(port=f.port).post(
            on='/search', inputs=Document(matches=[Document()]), return_responses=True
        )
    assert len(results[0].docs[0].matches) == num_shards


def test_merging_head_pod():
    port = random_port()

    def multimodal_generator():
        for i in range(0, 5):
            document = Document()
            document.chunks.append(Document(modality='1', content='1'))
            document.chunks.append(Document(modality='2', content='2'))
            yield document

    f = (
        Flow(port=port)
        .add(uses={'jtype': 'DummyExecutor', 'with': {'mode': '1'}}, name='executor1')
        .add(
            uses={'jtype': 'DummyExecutor', 'with': {'mode': '2'}},
            name='executor2',
            needs='gateway',
        )
        .add(
            uses_before=ChunkMerger, name='executor3', needs=['executor1', 'executor2']
        )
    )
    with f:
        results = Client(port=f.port).post(
            on='/search', inputs=multimodal_generator(), return_responses=True
        )
    assert len(results[0].docs[0].chunks) == 2
    assert len(results[0].docs) == 5
