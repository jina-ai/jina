from typing import Dict

from jina import Executor
from jina.excepts import ModelCheckpointNotExist


class DummyPretrainedExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise ModelCheckpointNotExist

    def craft(self, *args, **kwargs) -> Dict:
        pass
