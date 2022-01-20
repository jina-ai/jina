import numpy as np
import pytest

from jina import Document, DocumentArray, Flow, Executor, Client, requests

exposed_port = 12345


class ShardsExecutor(Executor):
    def __init__(self, n_docs: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.n_docs = n_docs

    @requests(on='/search')
    def search(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.matches.extend(
                [
                    Document(id=f'm-{self.runtime_args.pea_id}-{i}')
                    for i in range(self.n_docs)
                ]
            )
            doc.chunks.extend(
                [
                    Document(id=f'c-{self.runtime_args.pea_id}-{i}')
                    for i in range(self.n_docs)
                ]
            )

            doc.text = self.runtime_args.name

            if self.runtime_args.pea_id == 0:
                doc.scores['cosine'].value = 0
                doc.modality = 'text'
            elif self.runtime_args.pea_id == 1:
                doc.modality = 'image'
                doc.tags = {'c': 'd'}
            elif self.runtime_args.pea_id == 2:
                doc.tags = {'a': 'b'}


class DummyExecutor(Executor):
    @requests
    def fake_reduce(self, **kwargs):
        return DocumentArray([Document(id='fake_document')])


@pytest.mark.parametrize('n_docs', [3, 5])
def test_reduce_shards(n_docs):
    n_shards = 3
    search_flow = Flow(port_expose=exposed_port).add(
        uses=ShardsExecutor,
        shards=n_shards,
        polling='all',
        uses_with={'n_docs': n_docs},
    )

    with search_flow as f:
        da = DocumentArray([Document() for _ in range(5)])
        resp = Client(port=exposed_port).post('/search', inputs=da, return_results=True)

    assert len(resp[0].docs) == 5

    for doc in resp[0].docs:

        # assert matches and chunks are combined
        matches = set([doc.id for doc in doc.matches])
        chunks = set([doc.id for doc in doc.chunks])
        assert len(matches) == n_docs * n_shards
        assert len(chunks) == n_docs * n_shards
        for shard in range(n_shards):
            for match in range(n_docs):
                assert f'm-{shard}-{match}' in matches
            for chunk in range(n_docs):
                assert f'c-{shard}-{chunk}' in chunks

        # assert data properties are reduced with priority to the first shards
        assert doc.text == 'executor0/shard-0/rep-0'
        assert doc.scores['cosine'].value == 0
        assert doc.modality == 'text'
        assert doc.tags == {'c': 'd'}


@pytest.mark.parametrize('n_shards', [3, 5])
@pytest.mark.parametrize('n_docs', [3, 5])
def test_uses_after_no_reduce(n_shards, n_docs):
    search_flow = Flow(port_expose=exposed_port).add(
        uses=ShardsExecutor,
        shards=n_shards,
        uses_after=DummyExecutor,
        polling='all',
        uses_with={'n_docs': n_docs},
    )

    with search_flow as f:
        da = DocumentArray([Document() for _ in range(5)])
        resp = Client(port=exposed_port).post('/search', inputs=da, return_results=True)

    # assert no reduce happened
    assert len(resp[0].docs) == 1
    assert resp[0].docs[0].id == 'fake_document'


class Executor1(Executor):
    @requests
    def endpoint(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.text = 'exec1'


class Executor2(Executor):
    @requests
    def endpoint(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.tags = {'a': 'b'}
            doc.modality = 'image'


class Executor3(Executor):
    @requests
    def endpoint(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.embedding = np.zeros(3)


def test_reduce_needs():
    flow = (
        Flow(port_expose=exposed_port)
        .add(uses=Executor1, name='pod0')
        .add(uses=Executor2, needs='gateway', name='pod1')
        .add(uses=Executor3, needs='gateway', name='pod2')
        .add(needs=['pod0', 'pod1', 'pod2'], name='pod3')
    )

    with flow as f:
        da = DocumentArray([Document() for _ in range(5)])
        resp = Client(port=exposed_port).post('/', inputs=da, return_results=True)

    assert len(resp[0].docs) == 5
    for doc in resp[0].docs:
        assert doc.text == 'exec1'
        assert doc.tags == {'a': 'b'}
        assert doc.modality == 'image'
        assert (doc.embedding == np.zeros(3)).all()


def test_uses_before_reduce():
    flow = (
        Flow(port_expose=exposed_port)
        .add(uses=Executor1, name='pod0')
        .add(uses=Executor2, needs='gateway', name='pod1')
        .add(uses=Executor3, needs='gateway', name='pod2')
        .add(needs=['pod0', 'pod1', 'pod2'], name='pod3', uses_before='BaseExecutor')
    )

    with flow as f:
        da = DocumentArray([Document() for _ in range(5)])
        resp = Client(port=exposed_port).post('/', inputs=da, return_results=True)

    # assert reduce happened because there is only BaseExecutor as uses_before
    assert len(resp[0].docs) == 5


def test_uses_before_no_reduce_real_executor():
    flow = (
        Flow(port_expose=exposed_port)
        .add(uses=Executor1, name='pod0')
        .add(uses=Executor2, needs='gateway', name='pod1')
        .add(uses=Executor3, needs='gateway', name='pod2')
        .add(needs=['pod0', 'pod1', 'pod2'], name='pod3', uses_before=DummyExecutor)
    )

    with flow as f:
        da = DocumentArray([Document() for _ in range(5)])
        resp = Client(port=exposed_port).post('/', inputs=da, return_results=True)

    # assert no reduce happened
    assert len(resp[0].docs) == 1
    assert resp[0].docs[0].id == 'fake_document'


def test_uses_before_no_reduce_real_executor_uses():
    flow = (
        Flow(port_expose=exposed_port)
        .add(uses=Executor1, name='pod0')
        .add(uses=Executor2, needs='gateway', name='pod1')
        .add(uses=Executor3, needs='gateway', name='pod2')
        .add(needs=['pod0', 'pod1', 'pod2'], name='pod3', uses=DummyExecutor)
    )

    with flow as f:
        da = DocumentArray([Document() for _ in range(5)])
        resp = Client(port=exposed_port).post('/', inputs=da, return_results=True)

    # assert no reduce happened
    assert len(resp[0].docs) == 1
    assert resp[0].docs[0].id == 'fake_document'
