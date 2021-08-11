import pytest

from jina import Document, Executor, Flow, requests


class SimplExecutor(Executor):
    @requests
    def add_text(self, docs, **kwargs):
        docs[0].text = 'Hello World!'


def test_simple_routing():
    f = Flow().add(uses=SimplExecutor)
    with f:
        results = f.post(on='/index', inputs=[Document()], return_results=True)
        assert results[0].docs[0].text == 'Hello World!'


class MergeExecutor(Executor):
    @requests
    def add_text(self, docs, docs_matrix, **kwargs):
        if {docs[0].text, docs[1].text} == {'Hello World!', '1'}:
            docs[0].text = str(len(docs_matrix))


@pytest.mark.parametrize(
    'use_grpc',
    [True, False],
)
@pytest.mark.skip
def test_expected_messages_routing(use_grpc):
    f = (
        Flow(grpc_data_requests=use_grpc)
        .add(name='foo', uses=SimplExecutor)
        .add(name='bar', uses=MergeExecutor, needs=['foo', 'gateway'])
    )

    with f:
        results = f.post(on='/index', inputs=[Document(text='1')], return_results=True)
        assert results[0].docs[0].text == '2'
