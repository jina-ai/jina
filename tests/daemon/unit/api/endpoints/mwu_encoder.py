from typing import Any

from jina import Executor, requests


class MWUEncoder(Executor):
    @requests
    def encode(self, *args, **kwargs) -> Any:
        pass
