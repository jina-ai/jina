from jina import Executor, requests


class MyExecutorToReload1(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @requests()
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'MyExecutorAfterReload'

    @requests(on='/bar')
    def bar(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'MyExecutorAfterReloadBar'
