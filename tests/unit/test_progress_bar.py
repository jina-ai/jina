import time

import pytest
from jina.logging.profile import ProgressBar


@pytest.mark.parametrize('total_steps', [0, 1, 100])
@pytest.mark.parametrize('update_tick', [1, 0.1, 0.5])
@pytest.mark.parametrize('task_name', ['test', ''])
@pytest.mark.parametrize('msg_on_done', ['', 'done!', lambda task: 'done!'])
def test_progressbar(total_steps, update_tick, task_name, capsys, msg_on_done):
    with ProgressBar(
        description=task_name, message_on_done=msg_on_done, total_length=total_steps
    ) as pb:
        for j in range(total_steps):
            pb.update(advance=update_tick)
            time.sleep(0.001)

    captured = capsys.readouterr()
    assert 'ETA' in captured.out
