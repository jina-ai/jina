from jina import Executor, requests


class A(Executor):
    @requests
    def x(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'ABeforeReload'


class EnhancedExecutor(A):
    @requests
    def y(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'EnhancedBeforeReload'
