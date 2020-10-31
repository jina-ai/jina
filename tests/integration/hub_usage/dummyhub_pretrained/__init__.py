from typing import Dict

from jina.excepts import ModelCheckpointNotExist
from jina.executors.crafters import BaseCrafter


class DummyPretrainedExecutor(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_init(self):
        raise ModelCheckpointNotExist

    def craft(self, *args, **kwargs) -> Dict:
        pass
