import time

from typing import Any

from jina import Executor, requests, DocumentArray


class CustomExecutor(Executor):
    def foo(self, docs: DocumentArray, *args, **kwargs) -> Any:
        for d in docs.traverse_flat(['r']):
            d.text += 'foo'

    def bar(self, docs: DocumentArray, *args, **kwargs) -> Any:
        for d in docs.traverse_flat(['r']):
            d.text += 'bar'
