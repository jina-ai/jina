import time

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


@pytest.mark.parametrize(
    'use_grpc',
    [True],
)
def test_expected_messages_routing(use_grpc):
    f = (
        Flow(grpc_data_requests=use_grpc)
        .add(name='foo', uses=SimplExecutor)
        .add(name='bar', needs=['foo', 'gateway'])
    )

    with f:
        results = f.post(on='/index', inputs=[Document()], return_results=True)
        assert results[0].docs[0].text == 'Hello World!'


@pytest.mark.parametrize(
    'use_grpc',
    [True, False],
)
def test_static_routing_table_setup(use_grpc):
    f = (
        Flow(static_routing_table=True, grpc_data_requests=use_grpc)
        .add(name='foo', uses=SimplExecutor)
        .add(name='bar', needs=['foo', 'gateway'])
    )

    with f:
        results = f.post(on='/index', inputs=[Document()], return_results=True)
        assert results[0].docs[0].text == 'Hello World!'


class SimplAddExecutor(Executor):
    @requests
    def add_doc(self, docs, **kwargs):
        docs.append(Document(text=self.runtime_args.name))


def test_static_routing_table_shards():
    f = Flow(static_routing_table=True).add(uses=SimplAddExecutor, shards=2)

    with f:
        results = f.post(on='/index', inputs=[Document(text='1')], return_results=True)
        assert len(results[0].docs) == 2


def test_static_routing_table_complex_flow():
    f = (
        Flow(static_routing_table=True)
        .add(name='first', uses=SimplAddExecutor, needs=['gateway'])
        .add(name='forth', uses=SimplAddExecutor, needs=['first'], shards=2)
        .add(
            name='second_shards_needs',
            uses=SimplAddExecutor,
            needs=['gateway'],
            shards=2,
        )
        .add(
            name='third',
            uses=SimplAddExecutor,
            shards=3,
            needs=['second_shards_needs'],
        )
        .add(name='merger', needs=['forth', 'third'])
    )

    with f:
        results = f.post(on='/index', inputs=[Document(text='1')], return_results=True)
    assert len(results[0].docs) == 5
