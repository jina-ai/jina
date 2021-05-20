from typing import Any

from jina.executors.decorators import requests
from jina.executors import BaseExecutor


class MWUEncoder(BaseExecutor):
    def __init__(self, greetings: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._greetings = greetings

    @requests
    def encode(self, **kwargs) -> Any:
        pass
