import time

import pytest

from jina.logging.profile import ProgressBar


@pytest.mark.parametrize('total_steps', [0, 1, 10, 100])
@pytest.mark.parametrize('update_tick', [1, 4, 0.1, 0.5])
@pytest.mark.parametrize('task_name', [None, 'test', ''])
@pytest.mark.parametrize('details', [None, 'step {}'])
def test_progressbar(total_steps, update_tick, task_name, capsys, details):
    with ProgressBar(task_name) as pb:
        for j in range(total_steps):
            pb.update(update_tick, details=details.format(j) if details else None)
            time.sleep(0.001)

    captured = capsys.readouterr()
    if total_steps:
        assert 'steps done' in captured.out
    else:
        assert 'estimating' in captured.out
        assert 'steps done' not in captured.out


def test_never_call_update(capsys):
    with ProgressBar():
        pass
    captured = capsys.readouterr()
    assert captured.out.endswith(ProgressBar.clear_line)
