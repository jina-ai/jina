from jina import Executor, requests


class MyExecutorBeforeReload(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @requests()
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'MyExecutorBeforeReload'
