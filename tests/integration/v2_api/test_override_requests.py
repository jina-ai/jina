from jina import Client, Document, DocumentArray, Executor, Flow, requests

exposed_port = 12345


def test_override_requests():
    class FooExecutor(Executor):
        @requests(on='/foo')
        def foo(self, docs, **kwargs):
            for doc in docs:
                doc.text = 'foo called'

    with Flow(port=exposed_port).add(
        uses=FooExecutor, uses_requests={'/non_foo': 'foo'}
    ) as f:
        c = Client(port=exposed_port, return_responses=True)
        resp1 = c.post(on='/foo', inputs=DocumentArray([Document(text='')]))
        resp2 = c.post(
            on='/non_foo',
            inputs=DocumentArray([Document(text='')]),
        )

    assert resp1[0].docs[0].text == ''
    assert resp2[0].docs[0].text == 'foo called'


def test_override_requests_uses_after():
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

    with Flow(port=exposed_port).add(
        uses=FooExecutor,
        uses_requests={'/foo': 'foo'},
        shards=2,
        polling='ANY',
        uses_after=OtherExecutor,
        uses_before=OtherExecutor,
    ) as f:
        c = Client(port=exposed_port, return_responses=True)
        resp1 = c.post(on='/foo', inputs=DocumentArray([Document(text='')]))
        resp2 = c.post(
            on='/non_foo',
            inputs=DocumentArray([Document(text='')]),
        )
        resp3 = c.post(on='/bar', inputs=DocumentArray([Document(text='')]))

    assert resp1[0].docs[0].text == 'foo called'
    assert resp2[0].docs[0].text == ''
    assert resp3[0].docs[0].text == 'bar called'
