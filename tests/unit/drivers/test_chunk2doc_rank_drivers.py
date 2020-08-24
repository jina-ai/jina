from jina.drivers.rank import Chunk2DocRankDriver
from jina.executors.rankers import Chunk2DocRanker
from jina.hub.rankers.MaxRanker import MaxRanker
from jina.hub.rankers.MinRanker import MinRanker
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
    # doc: 1
    # |- chunk: 2
    # |  |- matches: (id: 4, parent_id: 40, score.value: 4),
    # |  |- matches: (id: 5, parent_id: 50, score.value: 5),
    # |
    # |- chunk: 3
    #    |- matches: (id: 6, parent_id: 60, score.value: 6),
    #    |- matches: (id: 7, parent_id: 70, score.value: 7)
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


def create_chunk_matches_to_score():
    # doc: (id: 100, level_depth=0)
    # |- chunks: (id: 10)
    # |  |- matches: (id: 11, parent_id: 1, score.value: 2, level_depth=1),
    # |  |- matches: (id: 12, parent_id: 1, score.value: 3, level_depth=1),
    # |- chunks: (id: 20)
    #    |- matches: (id: 21, parent_id: 2, score.value: 4, level_depth=1),
    #    |- matches: (id: 22, parent_id: 2, score.value: 5, level_depth=1)
    doc = jina_pb2.Document()
    doc.id = 100
    doc.level_depth = 0
    num_matches = 2
    for parent_id in range(1, 3):
        chunk = doc.chunks.add()
        chunk.id = parent_id * 10
        chunk.level_depth = doc.level_depth + 1
        for score_value in range(parent_id * 2, parent_id * 2 + num_matches):
            match = chunk.matches.add()
            match.level_depth = chunk.level_depth
            match.parent_id = parent_id
            match.score.value = score_value
            match.score.ref_id = chunk.id
            match.id = 10 * parent_id + score_value
            match.length = 4
    return doc


class Chunk2DocRankerDriverTestCase(JinaTestCase):

    def test_chunk2doc_ranker_driver_mock_exec(self):
        doc = create_document_to_score()
        driver = SimpleChunk2DocRankDriver()
        executor = MockLengthRanker()
        driver.attach(executor=executor, pea=None)
        driver._apply_all(doc.chunks, doc)
        assert len(doc.matches) == 4
        assert doc.matches[0].id == 70
        assert doc.matches[0].score.value == 7
        assert doc.matches[1].id == 60
        assert doc.matches[1].score.value == 6
        assert doc.matches[2].id == 50
        assert doc.matches[2].score.value == 5
        assert doc.matches[3].id == 40
        assert doc.matches[3].score.value == 4
        for match in doc.matches:
            # match score is computed w.r.t to doc.id
            assert match.score.ref_id == doc.id

    def test_chunk2doc_ranker_driver_MaxRanker(self):
        doc = create_document_to_score()
        driver = SimpleChunk2DocRankDriver()
        executor = MaxRanker()
        driver.attach(executor=executor, pea=None)
        driver._apply_all(doc.chunks, doc)
        assert len(doc.matches) == 4
        assert doc.matches[0].id == 70
        assert doc.matches[0].score.value == 7
        assert doc.matches[1].id == 60
        assert doc.matches[1].score.value == 6
        assert doc.matches[2].id == 50
        assert doc.matches[2].score.value == 5
        assert doc.matches[3].id == 40
        assert doc.matches[3].score.value == 4
        for match in doc.matches:
            # match score is computed w.r.t to doc.id
            assert match.score.ref_id == doc.id

    def test_chunk2doc_ranker_driver_MinRanker(self):
        doc = create_document_to_score()
        driver = SimpleChunk2DocRankDriver()
        executor = MinRanker()
        driver.attach(executor=executor, pea=None)
        driver._apply_all(doc.chunks, doc)
        assert len(doc.matches) == 4
        assert doc.matches[0].id == 40
        self.assertAlmostEqual(doc.matches[0].score.value, 1 / (1 + 4))
        assert doc.matches[1].id == 50
        self.assertAlmostEqual(doc.matches[1].score.value, 1 / (1 + 5))
        assert doc.matches[2].id == 60
        self.assertAlmostEqual(doc.matches[2].score.value, 1 / (1 + 6))
        assert doc.matches[3].id == 70
        self.assertAlmostEqual(doc.matches[3].score.value, 1 / (1 + 7))
        for match in doc.matches:
            # match score is computed w.r.t to doc.id
            assert match.score.ref_id == doc.id

    def test_chunk2doc_ranker_driver_traverse_apply(self):
        docs = [create_chunk_matches_to_score(), ]
        driver = SimpleChunk2DocRankDriver(depth_range=(0, 1))
        executor = MinRanker()
        driver.attach(executor=executor, pea=None)
        driver._traverse_apply(docs)
        for doc in docs:
            assert len(doc.matches) == 2
            for idx, m in enumerate(doc.matches):
                # the score should be 1 / (1 + id * 2)
                self.assertAlmostEqual(m.score.value, 1. / (1 + m.id * 2.))
                assert m.level_depth == 0
