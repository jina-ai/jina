from typing import Optional

from docarray import Document, DocumentArray

from jina import Executor, Flow, requests


def test_optional_type_hint():
    class MyExec(Executor):
        @requests
        def foo(self, docs: Optional[DocumentArray], **kwargs):
            return docs

    with Flow().add(uses=MyExec) as f:
        f.post('/', inputs=Document())
