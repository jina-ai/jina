from jina.executors.rankers.tfidf import BM25Ranker
from tests.unit.executors.rankers import RankerTestCase


class BM25TestCase(RankerTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ranker = BM25Ranker()
