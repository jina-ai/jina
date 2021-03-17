import time

from jina.executors.decorators import as_ndarray
from jina.executors.encoders import BaseEncoder


class DelayedExecutor(BaseEncoder):
    def post_init(self):
        self.logger.info('sleeping for 8 secs')
        time.sleep(8)

    @as_ndarray
    def encode(self, data, *args, **kwargs):
        return [[1, 2]] * len(data)
