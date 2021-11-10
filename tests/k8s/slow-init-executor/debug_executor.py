import time

from jina import Executor


class SlowInitExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from jina.logging.logger import JinaLogger

        self.logger = JinaLogger(self.__class__.__name__)
        self.logger.debug('Start sleep in SlowInitExecutor')
        time.sleep(10.0)
        self.logger.debug('Sleep over in SlowInitExecutor')
