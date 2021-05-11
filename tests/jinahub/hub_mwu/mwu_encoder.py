from typing import Any

from jina import Executor, requests


class MWUEncoder(Executor):
    def __init__(self, greetings: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._greetings = greetings

    @requests
    def encode(self, **kwargs) -> Any:
        pass
