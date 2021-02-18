import time

from jina.logging.profile import TimeDict


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
