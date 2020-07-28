import os

from jina.proto import jina_pb2
from jina.drivers.rank import Chunk2DocRankDriver
from jina.executors.rankers import Chunk2DocRanker
from tests import JinaTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))


class MockLengthRanker(Chunk2DocRanker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_keys = {'length'}

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return match_idx[0][1], match_chunk_meta[match_idx[0][0]]['length']


class SimpleChunk2DocRankDriver(Chunk2DocRankDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


class Chunk2DocRankerDriverTestCase(JinaTestCase):

    def test_chunk2doc_ranker_driver_mock_exec(self):
        driver = SimpleChunk2DocRankDriver()
        # doc: 1 - chunk: 2 - match: 4, 5
        #        - chunk: 3 - match: 6, 7
        doc = jina_pb2.Document()
        doc.id = 1
        for c in range(2):
            chunk = doc.chunks.add()
            chunk.id = doc.id + c + 1
            for m in range(2):
                match = chunk.matches.add()
                match.id = 2 * chunk.id + m
                match.parent_id = 10 * match.id
                match.score.ref_id = chunk.id
                match.length = match.id

        executor = MockLengthRanker()
        driver.attach(executor=executor, pea=None)
        driver._apply(doc)
        self.assertEqual(len(doc.matches), 4)
        self.assertEqual(doc.matches[0].id, 70)
        self.assertEqual(doc.matches[0].score.value, 7)
        self.assertEqual(doc.matches[1].id, 60)
        self.assertEqual(doc.matches[1].score.value, 6)
        self.assertEqual(doc.matches[2].id, 50)
        self.assertEqual(doc.matches[2].score.value, 5)
        self.assertEqual(doc.matches[3].id, 40)
        self.assertEqual(doc.matches[3].score.value, 4)
        for match in doc.matches:
            # match score is computed w.r.t to doc.id
            self.assertEqual(match.score.ref_id, doc.id)
