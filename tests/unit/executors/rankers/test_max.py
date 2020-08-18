from jina.hub.rankers import MaxRanker
from tests.unit.executors.rankers import RankerTestCase


class MaxRankerTestCase(RankerTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ranker = MaxRanker()
