import time

import pytest
from jina.enums import ProgressBarStatus
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


def test_error_in_progress_bar(capsys):
    with pytest.raises(NotImplementedError):
        with ProgressBar('update') as p:
            for j in range(100):
                p.update()
                time.sleep(0.01)
                if j > 5:
                    raise NotImplementedError
    captured = capsys.readouterr()
    assert str(ProgressBarStatus.ERROR) in captured.out


def test_kb_interrupt_in_progress_bar(capsys):
    with ProgressBar('update') as p:
        for j in range(100):
            p.update()
            time.sleep(0.01)
            if j > 5:
                raise KeyboardInterrupt
    captured = capsys.readouterr()
    assert str(ProgressBarStatus.CANCELED) in captured.out
