import time
from typing import Any


from jina.executors.encoders import BaseEncoder


class DelayedExecutor(BaseEncoder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = 'delayed-executor'

    def post_init(self):
        self.logger.info('sleeping for 8 secs')
        time.sleep(8)

    def encode(self, data: Any, *args, **kwargs) -> Any:
        return data
