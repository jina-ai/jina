import time

import pytest

from jina.excepts import RuntimeFailToStart
from jina.executors import BaseExecutor
from jina import Flow
from jina.logging.profile import TimeContext


class SlowExecutor(BaseExecutor):
    def post_init(self):
        time.sleep(4)


def test_flow_slow_executor_intra():
    f = Flow().add(uses='SlowExecutor', parallel=2)

    with f, TimeContext('start flow') as tc:
        assert tc.now() < 8


def test_flow_slow_executor_inter():
    f = Flow().add(uses='SlowExecutor', parallel=3).add(uses='SlowExecutor', parallel=3)

    with f, TimeContext('start flow') as tc:
        assert tc.now() < 8


def test_flow_slow_executor_bad_fail_early():
    f = (
        Flow()
        .add(uses='SlowExecutor', parallel=3)
        .add(uses='BADNAME_EXECUTOR', parallel=3)
    )

    with pytest.raises(RuntimeFailToStart):
        with f, TimeContext('start flow') as tc:
            assert tc.now() < 8
