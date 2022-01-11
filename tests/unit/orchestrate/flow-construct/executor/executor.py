from jina import Executor, DocumentArray, requests


class CustomExec(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.text = 'done'
