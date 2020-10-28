from typing import Dict

from jina.executors.crafters import BaseCrafter
from jina.excepts import ModelCheckpointNotExist


class DummyPretrainedExecutor(BaseCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_init(self):
        raise ModelCheckpointNotExist

    def craft(self, *args, **kwargs) -> Dict:
        pass

