import time

from jina.executors import BaseExecutor


class DelayedExecutor(BaseExecutor):
    def post_init(self):
        self.logger.info('sleeping for 8 secs')
        time.sleep(8)

    def encode(self, **kwargs):
        pass
