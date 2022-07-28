import pytest
from docarray import DocumentArray

from jina import Client, Document, Executor, Flow, requests, types
from jina.excepts import BadServer


class SimplExecutor(Executor):
    @requests
    def add_text(self, docs, **kwargs):
        docs[0].text = 'Hello World!'


def test_simple_docarray_return():
    f = Flow().add(uses=SimplExecutor)
    with f:
        docs = f.post(on='/index', inputs=[Document()])
    assert docs[0].text == 'Hello World!'


def test_flatten_docarrays():
    f = Flow().add(uses=SimplExecutor)
    with f:
        docs = f.post(
            on='/index',
            inputs=[Document() for _ in range(100)],
            request_size=10,
        )
    assert isinstance(docs, DocumentArray)
    assert len(docs) == 100
    assert docs[0].text == 'Hello World!'


def my_cb(resp):
    return resp


@pytest.mark.parametrize('on_done', [None, my_cb])
@pytest.mark.parametrize('on_always', [None, my_cb])
@pytest.mark.parametrize('on_error', [None, my_cb])
def test_automatically_set_returnresults(on_done, on_always, on_error):
    f = Flow().add(uses=SimplExecutor)
    with f:
        docs = f.post(
            on='/index',
            inputs=[Document() for _ in range(100)],
            request_size=10,
            on_done=on_done,
            on_always=on_always,
            on_error=on_error,
        )
    if on_done is None and on_always is None:
        assert isinstance(docs, DocumentArray)
        assert len(docs) == 100
        assert docs[0].text == 'Hello World!'
    else:
        assert docs is None


def test_empty_docarray():
    f = Flow().add(uses=SimplExecutor)
    with pytest.raises(BadServer):
        with f:
            f.post(on='/')


def test_flow_client_defaults(port_generator):
    exposed_port = port_generator()
    f = Flow(port=exposed_port).add(uses=SimplExecutor)
    c = Client(port=exposed_port)
    with f:
        docs = f.post(on='/index', inputs=[Document()])
        results = c.post(on='/index', inputs=[Document()])
    assert isinstance(docs, DocumentArray)
    assert docs[0].text == 'Hello World!'
    assert isinstance(results, DocumentArray)
    assert results[0].text == 'Hello World!'
