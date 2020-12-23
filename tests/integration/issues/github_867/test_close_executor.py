import os
import time
from typing import Any

from jina import Document
from jina.executors import BaseExecutor
from jina.executors.encoders import BaseEncoder
from jina.flow import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))
save_abs_path = os.path.join(cur_dir, 'slow-save-executor.bin')


class SlowSaveExecutor(BaseEncoder):
    """
    Github issue: https://github.com/jina-ai/jina/issues/867 and https://github.com/jina-ai/jina/issues/873

    Problem that user encountered is that his `indexer` was a little slow to save because `key_bytes` is large.
    Then, Pea closing logic was wrong and Flow was killing its Pods before they were able to properly close its resources.
    because they were running as `daemon` processes.

    This test tries to be a single proxy to that issue simulating via `sleep` an expensive pickling operation.
    Before https://github.com/jina-ai/jina/pull/907 this test would fail because at loading time no pickle object would be properly closed.
    This is similar to the case seen by the user where the `index` files are not properly flushed and closed.
    """

    def encode(self, data: Any, *args, **kwargs) -> Any:
        self.touch()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = 'slow-save-executor'

    @property
    def save_abspath(self) -> str:
        return save_abs_path

    def __getstate__(self):
        d = super().__getstate__()
        time.sleep(2)
        d['test'] = 10
        return d


def test_close_and_load_executor():
    with Flow().add(uses=os.path.join(cur_dir, 'yaml/slowexecutor.yml')) as f:
        f.index(['abc', 'def'])

    exec = BaseExecutor.load(save_abs_path)

    assert isinstance(exec, SlowSaveExecutor)
    assert hasattr(exec, 'test')
    assert exec.test == 10
    assert exec.save_abspath == save_abs_path
    os.remove(save_abs_path)
