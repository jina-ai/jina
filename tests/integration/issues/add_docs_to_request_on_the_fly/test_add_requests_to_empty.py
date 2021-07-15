from jina import Document, DocumentArray, Executor, Flow, requests


class AddToEmpty(Executor):
    @requests
    def foo(self, docs, **kwargs):
        docs.extend([Document(text='added document')])


def test_add_docs_to_request():
    with Flow().add(uses=AddToEmpty) as f:
        resps = f.post(on='/foo', inputs=DocumentArray([]), return_results=True)
        assert len(resps[0].docs) == 1
        assert resps[0].docs[0].text == 'added document'
