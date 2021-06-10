import os
import time

from jina import Flow, Executor


class SlowExecutor(Executor):
    def close(self) -> None:
        with open(os.path.join(self.metas.workspace, 'test'), 'w') as f:
            time.sleep(10)
            f.write('x')


def test_slow_executor_close(tmpdir):
    with Flow().add(
        uses={'jtype': 'SlowExecutor', 'with': {}, 'metas': {'workspace': str(tmpdir)}}
    ) as f:
        pass

    assert os.path.exists(os.path.join(tmpdir, 'test'))
