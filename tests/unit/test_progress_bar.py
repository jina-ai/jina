import time

import pytest

from jina.logging.profile import ProgressBar


@pytest.mark.parametrize('total_steps', [0, 1, 100])
@pytest.mark.parametrize('update_tick', [1, 0.1, 0.5])
@pytest.mark.parametrize('task_name', [None, 'test', ''])
@pytest.mark.parametrize('details', [None, 'step {}'])
@pytest.mark.parametrize('msg_on_done', [None, 'done!', lambda: 'done!'])
def test_progressbar(total_steps, update_tick, task_name, capsys, details, msg_on_done):
    with ProgressBar(description=task_name, message_on_done=msg_on_done) as pb:
        for j in range(total_steps):
            pb.update(update_tick, message=details.format(j) if details else None)
            time.sleep(0.001)

    captured = capsys.readouterr()
    assert 'estimating' in captured.out


def test_never_call_update(capsys):
    with ProgressBar():
        pass
    captured = capsys.readouterr()
    assert captured.out.endswith(ProgressBar.clear_line)
