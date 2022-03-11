from docarray import Document, DocumentArray
from jina import Executor, Flow, requests

import pytest


class SimplExecutor(Executor):
    @requests
    def add_text(self, docs, **kwargs):
        docs[0].text = 'Hello World!'


def test_simple_routing():
    f = Flow().add(uses=SimplExecutor)
    with f:
        docs = f.post(on='/index', inputs=[Document()])
        assert docs[0].text == 'Hello World!'


class MergeExecutor(Executor):
    @requests
    def add_text(self, docs, docs_matrix, **kwargs):
        if len(docs) == 2:
            docs[0].text = 'merged'


@pytest.mark.parametrize('disable_reduce', [True, False])
def test_expected_messages_routing(disable_reduce):
    f = (
        Flow()
        .add(name='foo', uses=SimplExecutor)
        .add(
            name='bar',
            uses=MergeExecutor,
            needs=['foo', 'gateway'],
            disable_reduce=disable_reduce,
        )
    )

    with f:
        docs = f.post(on='/index', inputs=[Document(text='1')])
        # there merge executor actually does not merge despite its name
        assert len(docs) == 2 if disable_reduce else 1
        assert docs[0].text == 'merged' if disable_reduce else '1'


class SimpleAddExecutor(Executor):
    @requests
    def add_doc(self, docs, **kwargs):
        docs.append(Document(text=self.runtime_args.name))


def test_shards():
    f = Flow().add(uses=SimpleAddExecutor, shards=2)

    with f:
        docs = f.post(on='/index', inputs=[Document(text='1')])
        assert len(docs) == 2


class MergeDocsExecutor(Executor):
    @requests
    def add_doc(self, docs, **kwargs):
        return docs


@pytest.mark.parametrize('disable_reduce', [True, False])
def test_complex_flow(disable_reduce):
    f = (
        Flow()
        .add(name='first', uses=SimpleAddExecutor, needs=['gateway'])
        .add(name='forth', uses=SimpleAddExecutor, needs=['first'], shards=2)
        .add(
            name='second_shards_needs',
            uses=SimpleAddExecutor,
            needs=['gateway'],
            shards=2,
        )
        .add(
            name='third',
            uses=SimpleAddExecutor,
            shards=3,
            needs=['second_shards_needs'],
        )
        .add(
            name='merger',
            uses=MergeDocsExecutor,
            needs=['forth', 'third'],
            disable_reduce=disable_reduce,
        )
    )

    with f:
        docs = f.post(on='/index', inputs=[Document(text='1')])
    assert len(docs) == 6 if disable_reduce else 5


class DynamicPollingExecutorDefaultNames(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='added'))
        return docs

    @requests(on='/search')
    def search(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='added'))
        return docs

    @requests(on='/custom')
    def custom(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='added'))
        return docs


@pytest.mark.parametrize('polling', ['any', 'all'])
def test_flow_default_polling_endpoints(polling):
    f = Flow().add(uses=DynamicPollingExecutorDefaultNames, shards=2, polling=polling)

    with f:
        docs_index = f.post(on='/index', inputs=[Document(text='1')])
        docs_search = f.post(on='/search', inputs=[Document(text='1')])
        docs_custom = f.post(on='/custom', inputs=[Document(text='1')])
    assert len(docs_index) == 2
    assert len(docs_search) == 3
    assert len(docs_custom) == 3 if polling == 'all' else 2


@pytest.mark.parametrize('polling', ['any', 'all'])
def test_flow_default_custom_polling_endpoints(polling):
    custom_polling_config = {'/custom': 'ALL', '/search': 'ANY', '*': polling}
    f = Flow().add(
        uses=DynamicPollingExecutorDefaultNames,
        shards=2,
        polling=custom_polling_config,
    )

    with f:
        docs_index = f.post(on='/index', inputs=[Document(text='1')])
        docs_search = f.post(on='/search', inputs=[Document(text='1')])
        docs_custom = f.post(on='/custom', inputs=[Document(text='1')])
    assert len(docs_index) == 2
    assert len(docs_search) == 2
    assert len(docs_custom) == 3
