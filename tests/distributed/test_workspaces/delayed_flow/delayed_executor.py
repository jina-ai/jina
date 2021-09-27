import time

from typing import Any

from jina import Executor, requests


class DelayedExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('sleeping for 5 secs')
        time.sleep(5)
        print('done sleeping')

    @requests
    def foo(self, *args, **kwargs) -> Any:
        pass
