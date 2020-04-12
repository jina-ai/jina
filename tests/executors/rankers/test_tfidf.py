import unittest

from jina.executors.rankers.tfidf import TfIdfRanker
from tests.executors.rankers import RankerTestCase


class MyTestCase(RankerTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ranker = TfIdfRanker()


if __name__ == '__main__':
    unittest.main()
