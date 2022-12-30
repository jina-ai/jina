import time

from jina import Executor

time.sleep(60)


class SlowLoadExecutor(Executor):
    pass
