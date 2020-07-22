import os
import time

from jina.executors.crafters import BaseCrafter


class SlowWorker(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # half of worker is slow
        self.is_slow = os.getpid() % 10 != 0
        self.logger.warning('im a slow worker')

    def craft(self, id, *args, **kwargs):
        if self.is_slow:
            self.logger.warning('slowly doing')
            time.sleep(2)
        return {'id': id}
