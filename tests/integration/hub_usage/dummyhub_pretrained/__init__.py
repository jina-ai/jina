from typing import Dict

from jina import Executor


class ModelCheckpointNotExist(FileNotFoundError):
    """Exception to raise for executors depending on pretrained model files when they do not exist."""


class DummyPretrainedExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise ModelCheckpointNotExist

    def craft(self, *args, **kwargs) -> Dict:
        pass
