from jina.logging.profile import TimeDict
import time


def test_logging_profile_timedict():
    td = TimeDict()
    td("timer")
    with td:
        time.sleep(2)

    assert int(td.accum_time["timer"]) == 2
    assert str(td) == "timer: 2.0s"
    td.reset()
    assert len(td.start_time) == 0
