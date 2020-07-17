import unittest

from jina.executors.rankers import MaxRanker
from tests.unit.executors.rankers import RankerTestCase


class MyTestCase(RankerTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ranker = MaxRanker()


if __name__ == '__main__':
    unittest.main()
