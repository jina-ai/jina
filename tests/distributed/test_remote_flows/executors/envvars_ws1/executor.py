from typing import Any

from jina import Executor, DocumentArray


class CustomExecutor(Executor):
    def foo(self, docs: DocumentArray, *args, **kwargs) -> Any:
        for d in docs:
            d.text += 'foo'

    def bar(self, docs: DocumentArray, *args, **kwargs) -> Any:
        for d in docs:
            d.text += 'bar'
