from jina import Client, Document, DocumentArray, Executor, Flow, requests
from jina.helper import random_port


def test_override_requests():
    port = random_port()

    class FooExecutor(Executor):
        @requests(on='/foo')
        def foo(self, docs, **kwargs):
            for doc in docs:
                doc.text = 'foo called'

    with Flow(port=port).add(
        uses=FooExecutor, uses_requests={'/non_foo': 'foo', '/another_foo': 'foo'}
    ) as f:
        c = Client(port=f.port)
        resp1 = c.post(
            on='/foo', inputs=DocumentArray([Document(text='')]), return_responses=True
        )
        resp2 = c.post(
            on='/non_foo',
            inputs=DocumentArray([Document(text='')]),
            return_responses=True,
        )
        resp3 = c.post(
            on='/another_foo',
            inputs=DocumentArray([Document(text='')]),
            return_responses=True,
        )

    assert resp1[0].docs[0].text == ''
    assert resp2[0].docs[0].text == 'foo called'
    assert resp3[0].docs[0].text == 'foo called'


def test_override_requests_uses_after():
    port = random_port()

    class FooExecutor(Executor):
        @requests(on='/bar')
        def foo(self, docs, **kwargs):
            for doc in docs:
                doc.text = 'foo called'

    class OtherExecutor(Executor):
        @requests(on='/bar')
        def bar(self, docs, **kwargs):
            for doc in docs:
                doc.text = 'bar called'

    with Flow(port=port).add(
        uses=FooExecutor,
        uses_requests={'/foo': 'foo'},
        shards=2,
        polling='ANY',
        uses_after=OtherExecutor,
        uses_before=OtherExecutor,
    ) as f:
        c = Client(port=f.port)
        resp1 = c.post(
            on='/foo', inputs=DocumentArray([Document(text='')]), return_responses=True
        )
        resp2 = c.post(
            on='/non_foo',
            inputs=DocumentArray([Document(text='')]),
            return_responses=True,
        )
        resp3 = c.post(
            on='/bar', inputs=DocumentArray([Document(text='')]), return_responses=True
        )

    assert resp1[0].docs[0].text == 'foo called'
    assert resp2[0].docs[0].text == ''
    assert resp3[0].docs[0].text == 'bar called'
