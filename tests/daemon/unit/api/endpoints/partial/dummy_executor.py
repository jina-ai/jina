from typing import Any

from jina import Executor, requests


class DummyExecutor(Executor):
    @requests
    def dummy_handle(self, docs, *args, **kwargs) -> Any:
        docs[0].content = "https://jina.ai"
        return docs
