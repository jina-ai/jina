from jina import Executor, requests


class RemoteFlowTestExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for idx, doc in enumerate(docs):
            doc.tags['counter'] = idx
