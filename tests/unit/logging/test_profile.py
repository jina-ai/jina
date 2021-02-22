import time

import pytest

from jina.logging import default_logger
from jina.logging.profile import TimeDict, profiling


@pytest.fixture
def default_logger_propagate():
    default_logger.logger.propagate = True
    yield
    default_logger.logger.propagate = False


def test_logging_profile_profiling(caplog, default_logger_propagate):
    @profiling
    def foo():
        time.sleep(1)
        temp_data = [i for i in range(0, 10000)]

    foo()
    # profiling format: JINA@79684[I]: foo time: 0.00042528799999996814s memory Δ 376.0 KB 47.3 MB -> 47.7 MB
    captured_list = caplog.text.split()
    assert captured_list[3] == 'time:'
    assert float(captured_list[4][:-1]) > 1
    assert captured_list[5] == 'memory'
    assert float(captured_list[7]) > 0


def test_logging_profile_timedict():
    td = TimeDict()
    td('timer')
    with td:
        time.sleep(2)

    assert int(td.accum_time['timer']) == 2
    assert str(td) == 'timer: 2.0s'

    td.reset()
    assert len(td.accum_time) == 0
    assert len(td.first_start_time) == 0
    assert len(td.start_time) == 0
    assert len(td.end_time) == 0
