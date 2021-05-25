import time

from jina import Executor


class DelayedExecutor(Executor):
    def post_init(self):
        print('sleeping for 8 secs')
        time.sleep(8)

    def encode(self, **kwargs):
        pass
