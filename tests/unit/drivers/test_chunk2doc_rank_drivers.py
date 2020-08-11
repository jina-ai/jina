from jina.drivers.rank import Chunk2DocRankDriver
from jina.executors.rankers import Chunk2DocRanker, MaxRanker, MinRanker
from jina.proto import jina_pb2
from tests import JinaTestCase


class MockLengthRanker(Chunk2DocRanker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_keys = {'length'}

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return match_idx[0][self.col_doc_id], match_chunk_meta[match_idx[0][self.col_chunk_id]]['length']


class SimpleChunk2DocRankDriver(Chunk2DocRankDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


def create_document_to_score():
    # doc: 1 - chunk: 2 - match: 4 (parent 40), 5 (parent 50)
    #        - chunk: 3 - match: 6 (parent 60), 7 (parent 70)
    doc = jina_pb2.Document()
    doc.id = 1
    for c in range(2):
        chunk = doc.chunks.add()
        chunk.id = doc.id + c + 1
        for m in range(2):
            match = chunk.matches.add()
            match.id = 2 * chunk.id + m
            match.parent_id = 10 * match.id
            match.length = match.id
            # to be used by MaxRanker and MinRanker
            match.score.ref_id = chunk.id
            match.score.value = match.id
    return doc


class Chunk2DocRankerDriverTestCase(JinaTestCase):

    def test_chunk2doc_ranker_driver_mock_exec(self):
        doc = create_document_to_score()
        driver = SimpleChunk2DocRankDriver()
        executor = MockLengthRanker()
        driver.attach(executor=executor, pea=None)
        driver._apply_all(doc.chunks, doc)
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

    def test_chunk2doc_ranker_driver_MaxRanker(self):
        doc = create_document_to_score()
        driver = SimpleChunk2DocRankDriver()
        executor = MaxRanker()
        driver.attach(executor=executor, pea=None)
        driver._apply_all(doc.chunks, doc)
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

    def test_chunk2doc_ranker_driver_MinRanker(self):
        doc = create_document_to_score()
        driver = SimpleChunk2DocRankDriver()
        executor = MinRanker()
        driver.attach(executor=executor, pea=None)
        driver._apply_all(doc.chunks, doc)
        self.assertEqual(len(doc.matches), 4)
        self.assertEqual(doc.matches[0].id, 40)
        self.assertAlmostEqual(doc.matches[0].score.value, 1 / (1 + 4))
        self.assertEqual(doc.matches[1].id, 50)
        self.assertAlmostEqual(doc.matches[1].score.value, 1 / (1 + 5))
        self.assertEqual(doc.matches[2].id, 60)
        self.assertAlmostEqual(doc.matches[2].score.value, 1 / (1 + 6))
        self.assertEqual(doc.matches[3].id, 70)
        self.assertAlmostEqual(doc.matches[3].score.value, 1 / (1 + 7))
        for match in doc.matches:
            # match score is computed w.r.t to doc.id
            self.assertEqual(match.score.ref_id, doc.id)

    def test_chunk2doc_ranker_driver_traverse_apply_MinRanker(self):
        docs = [create_document_to_score() for i in range(3)]
        driver = SimpleChunk2DocRankDriver()
        executor = MinRanker()
        driver.attach(executor=executor, pea=None)
        driver._traverse_apply(docs)
        for doc in docs:
            self.assertEqual(len(doc.matches), 4)
            self.assertEqual(doc.matches[0].id, 40)
            self.assertAlmostEqual(doc.matches[0].score.value, 1 / (1 + 4))
            self.assertEqual(doc.matches[1].id, 50)
            self.assertAlmostEqual(doc.matches[1].score.value, 1 / (1 + 5))
            self.assertEqual(doc.matches[2].id, 60)
            self.assertAlmostEqual(doc.matches[2].score.value, 1 / (1 + 6))
            self.assertEqual(doc.matches[3].id, 70)
            self.assertAlmostEqual(doc.matches[3].score.value, 1 / (1 + 7))
            for match in doc.matches:
                # match score is computed w.r.t to doc.id
                self.assertEqual(match.score.ref_id, doc.id)