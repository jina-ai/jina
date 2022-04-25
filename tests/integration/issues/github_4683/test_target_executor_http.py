import pytest

from docarray import Document
from jina import Executor, Flow, requests


@pytest.mark.parametrize('protocol', ['http', 'websocket'])
def test_good_entrypoint(protocol):
    class E1(Executor):
        @requests
        def foo(self, docs, **kwargs):
            docs.texts = ['hello']

    class E2(Executor):
        @requests
        def foo(self, docs, **kwargs):
            docs.texts = ['goodbye']

    f = Flow(protocol=protocol).add(name='m1', uses=E1).add(name='m2', uses=E2)

    with f:
        returned_texts = f.post('/', Document(), target_executor='m1').texts

    assert returned_texts == ['hello']
