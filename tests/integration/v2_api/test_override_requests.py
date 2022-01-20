from jina import DocumentArray, Executor, Flow, Client, requests, Document

exposed_port = 12345


def test_override_requests():
    class FooExecutor(Executor):
        @requests(on='/foo')
        def foo(self, docs, **kwargs):
            for doc in docs:
                doc.text = 'foo called'

    with Flow(port_expose=exposed_port).add(
        uses=FooExecutor, uses_requests={'/non_foo': 'foo'}
    ) as f:
        c = Client(port=exposed_port)
        resp1 = c.post(
            on='/foo', inputs=DocumentArray([Document(text='')]), return_results=True
        )
        resp2 = c.post(
            on='/non_foo',
            inputs=DocumentArray([Document(text='')]),
            return_results=True,
        )

    assert resp1[0].docs[0].text == ''
    assert resp2[0].docs[0].text == 'foo called'
