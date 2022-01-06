from docarray import DocumentArray
from jina import Document, Executor, Flow, requests

import pytest


class SimplExecutor(Executor):
    @requests
    def add_text(self, docs, **kwargs):
        docs[0].text = 'Hello World!'


def test_simple_docarray_return():
    f = Flow().add(uses=SimplExecutor)
    with f:
        results = f.post(on='/index', inputs=[Document()], return_results=True)
        assert results[0].text == 'Hello World!'


def test_flatten_docarrays():
    f = Flow().add(uses=SimplExecutor)
    with f:
        results = f.post(
            on='/index',
            inputs=[Document() for _ in range(100)],
            request_size=10,
            return_results=True,
        )
        assert isinstance(results, DocumentArray)
        assert len(results) == 100
        assert results[0].text == 'Hello World!'


def test_set_returnresults_true_without_callbacks():
    f = Flow().add(uses=SimplExecutor)
    with f:
        results = f.post(
            on='/index',
            inputs=[Document() for _ in range(100)],
            request_size=10,
            return_results=False,
        )
        assert isinstance(results, DocumentArray)
        assert len(results) == 100
        assert results[0].text == 'Hello World!'


def test_set_returnresults_true_onerror():
    f = Flow().add(uses=SimplExecutor)
    with f:
        results = f.post(
            on='/index',
            inputs=[Document() for _ in range(100)],
            request_size=10,
            return_results=False,
            on_error=lambda x: x,
        )
        assert isinstance(results, DocumentArray)
        assert len(results) == 100
        assert results[0].text == 'Hello World!'


def test_obey_returnresults_with_callbacks():
    f = Flow().add(uses=SimplExecutor)
    with f:
        results = f.post(
            on='/index',
            inputs=[Document() for _ in range(100)],
            request_size=10,
            return_results=False,
            on_done=lambda x: x,
        )
        assert results is None
    f = Flow().add(uses=SimplExecutor)
    with f:
        results = f.post(
            on='/index',
            inputs=[Document() for _ in range(100)],
            request_size=10,
            return_results=False,
            on_always=lambda x: x,
        )
        assert results is None
