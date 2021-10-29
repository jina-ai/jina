from jina import DocumentArray, Executor, Flow, requests, Document


def test_override_requests():
    class FooExecutor(Executor):
        @requests(on='/foo')
        def foo(self, docs, **kwargs):
            for doc in docs:
                doc.text = 'foo called'

    with Flow().add(uses=FooExecutor, uses_requests={'/non_foo': 'foo'}) as f:
        resp1 = f.post(
            on='/foo', inputs=DocumentArray([Document(text='')]), return_results=True
        )
        resp2 = f.post(
            on='/non_foo',
            inputs=DocumentArray([Document(text='')]),
            return_results=True,
        )

    assert resp1[0].docs[0].text == ''
    assert resp2[0].docs[0].text == 'foo called'
