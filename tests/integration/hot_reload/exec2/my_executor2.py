from jina import Executor, requests

from .helper import get_doc_value


class MyExecutorToReload2(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @requests()
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = get_doc_value()
