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
        print(1)
    foo()
    assert "memory" in caplog.text


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
