import os
import time

from jina.enums import SchedulerType
from jina.executors.crafters import BaseCrafter
from jina.flow import Flow
from tests import random_docs

os.environ['JINA_LOG_VERBOSITY'] = 'DEBUG'


class SlowWorker(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # half of worker is slow
        self.is_slow = os.getpid() % 2 != 0
        self.logger.warning('im a slow worker')

    def craft(self, id, *args, **kwargs):
        if self.is_slow:
            self.logger.warning('slowly doing')
            time.sleep(1)
        return {'id': id}


def test_lb():
    f = Flow(runtime='process').add(
        name='sw',
        uses='SlowWorker',
        parallel=10)
    with f:
        f.index(input_fn=random_docs(100), batch_size=10)


def test_roundrobin():
    f = Flow(runtime='process').add(
        name='sw',
        uses='SlowWorker',
        parallel=10, scheduling=SchedulerType.ROUND_ROBIN)
    with f:
        f.index(input_fn=random_docs(100), batch_size=10)
