import pytest
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


@pytest.fixture
def doc_with_score():
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

@pytest.fixture(
    scope="module",
    params=[
        MockLengthRanker(),
        MaxRanker(),
        MinRanker()
])
def ranker(request):
    return request.param

@pytest.fixture(scope="module")
def driver(ranker):
    driver = SimpleChunk2DocRankDriver()
    return driver.attach(executor=ranker, pea=None)

class Chunk2DocRankerDriverTestCase(JinaTestCase):

    def test_chunk2doc_ranker_driver_mock_exec(self, driver, doc_with_score):
        driver._apply_all(doc_with_score.chunks, doc_with_score)
        for match in doc_with_score.matches:
            # match score is computed w.r.t to doc.id
            self.assertEqual(match.score.ref_id, doc_with_score.id)

    @pytest.maxk.parameterize("index, expected", [
        (0, 7),
        (1, 6),
        (2, 5),
        (3, 4),
    ])
    def test_doc_score_chunk2doc_driver(self, index, expected, driver, doc_with_score):
        driver._apply_all(doc_with_score.chunks, doc_with_score)
        assert doc_with_score[index].score.value == expected

    @pytest.maxk.parameterize("index, expected", [
        (0, 70),
        (1, 60),
        (2, 50),
        (3, 40)
    ])
    def test_doc_id_chunk2doc_driver(self, index, expected, driver, doc_with_score):
        driver._apply_all(doc_with_score.chunks, doc_with_score)
        assert doc_with_score.matches[index].id == expected

