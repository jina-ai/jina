from typing import Dict

from jina.executors.crafters import BaseCrafter
from jina.excepts import PretrainedModelFileDoesNotExist


class DummyPretrainedExecutor(BaseCrafter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_init(self):
        raise PretrainedModelFileDoesNotExist

    def craft(self, *args, **kwargs) -> Dict:
        pass
