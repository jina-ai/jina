import unittest

from jina.executors.rankers.bi_match import BiMatchRanker
from tests.unit.executors.rankers import RankerTestCase


class MyTestCase(RankerTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ranker = BiMatchRanker()


if __name__ == '__main__':
    unittest.main()
