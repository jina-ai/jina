from jina import Executor, requests, DocumentArray


class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0].text = 'hello, world!'
        docs[1].text = 'goodbye, world!'
