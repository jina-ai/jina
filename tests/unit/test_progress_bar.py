import time

import pytest

from jina.logging.profile import ProgressBar


@pytest.mark.parametrize('total_steps', [0, 1, 10, 100])
@pytest.mark.parametrize('update_tick', [1, 4, 0.1, 0.5])
@pytest.mark.parametrize('task_name', [None, 'test', ''])
def test_progressbar(total_steps, update_tick, task_name, capsys):
    with ProgressBar(task_name) as pb:
        for j in range(total_steps):
            pb.update(update_tick)
            time.sleep(0.01)

    captured = capsys.readouterr()
    assert 'steps done' in captured.out
