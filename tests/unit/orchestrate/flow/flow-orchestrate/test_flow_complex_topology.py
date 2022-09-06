import threading
import multiprocessing
import time

import pytest

from jina import Document, Executor, Flow, helper, requests


@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_flow_complex_toploogy(protocol):
    f = (
        Flow(protocol=protocol)
        .add(name='p2', needs='gateway')
        .add(name='p3', needs='gateway')
        .add(name='p2p3joiner', needs=['p2', 'p3'])
        .add(name='p5', needs='p2p3joiner')
        .add(name='p6', needs='p2p3joiner')
        .add(name='p7', needs=['p5', 'p6'])
    )

    with f:
        res = f.index(Document())

    assert len(res) > 0


class FooExec(Executor):
    @requests
    def foo(self, docs, **kwargs):
        docs.texts = ['foo' for _ in docs]


def test_flow_external_executor_with_gateway():
    external_gateway_port = helper.random_port()

    def serve_exec(**kwargs):
        FooExec.serve(**kwargs)

    e = multiprocessing.Event()
    t = multiprocessing.Process(
        name='serve-exec',
        target=serve_exec,
        kwargs={'port': external_gateway_port, 'stop_event': e},
    )
    t.start()
    time.sleep(5)  # allow exec to start

    with Flow().add(
        name='external_gateway_exec', external=True, port=external_gateway_port
    ) as f:
        docs = f.search(Document())
        assert docs.texts == ['foo']

    e.set()
    t.terminate()
    t.join()


class BarExec(Executor):
    @requests
    def bar(self, docs, **kwargs):
        for doc in docs:
            doc.text += 'bar'


def test_flow_to_flow():
    with Flow().add(uses=FooExec) as external_flow:
        with Flow().add(external=True, port=external_flow.port).add(uses=BarExec) as f:
            docs = f.search(Document())
            assert docs.texts == ['foobar']


class AddBazExec(Executor):
    @requests
    def bar(self, docs, **kwargs):
        docs.append(Document(text='baz'))


def test_merging_external_executor_auto_reduce():
    with Flow().add(uses=BarExec) as external_flow:
        with Flow().add(uses=AddBazExec, name='exec1').add(
            uses=AddBazExec, name='exec2'
        ).add(external=True, port=external_flow.port, needs=['exec1', 'exec2']) as f:
            docs = f.search(Document(text='client'))
            assert docs.texts == ['clientbar', 'bazbar', 'bazbar']


def test_merging_external_executor_auto_reduce_disabled():
    with Flow().add(uses=BarExec) as external_flow:
        with pytest.raises(ValueError):
            with Flow().add(uses=AddBazExec, name='exec1').add(
                uses=AddBazExec, name='exec2'
            ).add(
                external=True,
                port=external_flow.port,
                needs=['exec1', 'exec2'],
                disable_reduce=True,
            ) as f:
                docs = f.search(Document(text='client'))
                assert docs.texts == ['clientbar', 'bazbar', 'bazbar']
