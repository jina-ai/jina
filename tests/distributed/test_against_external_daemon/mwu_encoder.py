from typing import Any

from jina import requests, Executor


class MWUEncoder(Executor):
    @requests
    def encode(self, **kwargs) -> Any:
        pass
