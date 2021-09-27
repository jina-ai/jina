from jina import Executor, DocumentArray, requests


class {{exec_name}}(Executor):
    """{{exec_description}}"""
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        pass