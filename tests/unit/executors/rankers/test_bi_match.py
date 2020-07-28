from jina.executors.rankers.bi_match import BiMatchRanker
from tests.unit.executors.rankers import RankerTestCase


class BiMatchTestCase(RankerTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ranker = BiMatchRanker()
