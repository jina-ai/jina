import time

import pytest

from jina.logging.predefined import default_logger
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

    foo()
    # profiling format: JINA@79684[I]: foo time: 0.00042528799999996814s memory Δ 376.0 KB 47.3 MB -> 47.7 MB
    assert 'time' in caplog.text


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
