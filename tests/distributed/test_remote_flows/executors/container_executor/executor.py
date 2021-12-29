from jina import Executor, requests


class ContainerExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for idx, doc in enumerate(docs):
            doc.tags['counter'] = idx
