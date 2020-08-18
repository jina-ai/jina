from jina.hub.rankers.tfidf import TfIdfRanker
from tests.unit.executors.rankers import RankerTestCase


class TfIdfRankerTestCase(RankerTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ranker = TfIdfRanker(threshold=0.2)
