import time

import pytest

from jina.logging.profile import ProgressBar


@pytest.mark.parametrize('total_steps', [1, 10, 100])
@pytest.mark.parametrize('update_tick', [1, 4, 0.1, 0.2])
@pytest.mark.parametrize('task_name', ['', 'test'])
def test_progressbar(total_steps, update_tick, task_name):
    with ProgressBar(task_name) as pb:
        for j in range(total_steps):
            pb.update(update_tick)
            time.sleep(0.01)
