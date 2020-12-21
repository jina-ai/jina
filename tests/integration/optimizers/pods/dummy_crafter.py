from typing import Dict
from jina.executors.crafters import BaseCrafter


class DummyCrafter(BaseCrafter):
    GOOD_PARAM_1 = 0
    GOOD_PARAM_2 = 3
    GOOD_PARAM_3 = 5

    def __init__(self,
                 param1: int,
                 param2: int,
                 param3: int,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.param1 = param1
        self.param2 = param2
        self.param3 = param3

    @property
    def good_params(self):
        return self.param1 == DummyCrafter.GOOD_PARAM_1 and self.param2 == DummyCrafter.GOOD_PARAM_2 and self.param3 == DummyCrafter.GOOD_PARAM_3

    def craft(self, text, *args, **kwargs) -> Dict:
        if self.good_params:
            return {'text': text}
        else:
            return {'text': ''}
