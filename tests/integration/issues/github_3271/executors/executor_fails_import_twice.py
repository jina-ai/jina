from jina import Executor, requests


class ExecutorImportedOnce(Executor):
    @requests
    def foo(self, **kwargs):
        pass
