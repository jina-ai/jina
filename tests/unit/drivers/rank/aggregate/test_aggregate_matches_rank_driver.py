import pytest

from jina import Document
from jina.drivers.rank.aggregate import AggregateMatches2DocRankDriver
from jina.executors.rankers import Chunk2DocRanker
from jina.types.score import NamedScore
from jina.types.arrays import DocumentArray


class MockMaxRanker(Chunk2DocRanker):
    def __init__(self, *args, **kwargs):
        super().__init__(
            query_required_keys=('length',),
            match_required_keys=('length',),
            *args,
            **kwargs,
        )

    def score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return match_idx[self.COL_SCORE].max()


class MockMinRanker(Chunk2DocRanker):
    def __init__(self, *args, **kwargs):
        super().__init__(
            query_required_keys=('length',),
            match_required_keys=('length',),
            *args,
            **kwargs,
        )

    def score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return 1.0 / (1.0 + match_idx[self.COL_SCORE].min())


class SimpleCollectMatchesRankDriver(AggregateMatches2DocRankDriver):
    def __init__(self, docs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = docs

    @property
    def exec_fn(self):
        return self._exec_fn

    @property
    def docs(self):
        return self._docs


class MockLengthRanker(Chunk2DocRanker):
    def __init__(self, *args, **kwargs):
        super().__init__(
            query_required_keys=('weight',),
            match_required_keys=('weight',),
            *args,
            **kwargs,
        )

    def score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return match_chunk_meta[match_idx[0][self.COL_DOC_CHUNK_ID]]['weight']


def create_document_to_score_same_depth_level():
    # doc: 1
    # |  matches: (id: 2, parent_id: 20, score.value: 30, length: 3),
    # |  matches: (id: 3, parent_id: 20, score.value: 40, length: 4),
    # |  matches: (id: 4, parent_id: 30, score.value: 20, length: 2),
    # |  matches: (id: 5, parent_id: 30, score.value: 10, length: 1),

    doc = Document()
    doc.id = 1

    for match_id, parent_id, match_score, weight in [
        (2, 20, 30, 3),
        (3, 20, 40, 4),
        (4, 30, 20, 2),
        (5, 30, 10, 1),
    ]:
        match = Document()
        match.id = match_id
        match.parent_id = parent_id
        match.weight = weight
        match.score = NamedScore(value=match_score, ref_id=doc.id)
        doc.matches.append(match)
    return doc


def test_collect_matches2doc_ranker_driver_mock_ranker():
    doc = create_document_to_score_same_depth_level()
    driver = SimpleCollectMatchesRankDriver(docs=DocumentArray([doc]))
    executor = MockLengthRanker()
    driver.attach(executor=executor, runtime=None)
    driver()
    dm = list(doc.matches)
    assert len(dm) == 2
    assert dm[0].id == '20'
    assert dm[0].score.value == 3.0
    assert dm[1].id == '30'
    assert dm[1].score.value == 2.0
    for match in dm:
        # match score is computed w.r.t to doc.id
        assert match.score.ref_id == doc.id


@pytest.mark.parametrize('keep_source_matches_as_chunks', [False, True])
def test_collect_matches2doc_ranker_driver_min_ranker(keep_source_matches_as_chunks):
    doc = create_document_to_score_same_depth_level()
    driver = SimpleCollectMatchesRankDriver(
        docs=DocumentArray([doc]),
        keep_source_matches_as_chunks=keep_source_matches_as_chunks,
    )
    executor = MockMinRanker()
    driver.attach(executor=executor, runtime=None)
    import sys

    min_value_30 = sys.maxsize
    min_value_20 = sys.maxsize
    for match in doc.matches:
        if match.parent_id == '30':
            if match.score.value < min_value_30:
                min_value_30 = match.score.value
        if match.parent_id == '20':
            if match.score.value < min_value_20:
                min_value_20 = match.score.value

    assert min_value_30 < min_value_20
    driver()
    dm = list(doc.matches)
    assert len(dm) == 2
    assert dm[0].id == '30'
    assert dm[0].score.value == pytest.approx((1.0 / (1.0 + min_value_30)), 0.0000001)
    assert dm[1].id == '20'
    assert dm[1].score.value == pytest.approx((1.0 / (1.0 + min_value_20)), 0.0000001)
    for match in dm:
        # match score is computed w.r.t to doc.id
        assert match.score.ref_id == doc.id
        expected_chunk_matches_length = 2 if keep_source_matches_as_chunks else 0
        assert len(match.chunks) == expected_chunk_matches_length


@pytest.mark.parametrize('keep_source_matches_as_chunks', [False, True])
def test_collect_matches2doc_ranker_driver_max_ranker(keep_source_matches_as_chunks):
    doc = create_document_to_score_same_depth_level()
    driver = SimpleCollectMatchesRankDriver(
        docs=DocumentArray([doc]),
        keep_source_matches_as_chunks=keep_source_matches_as_chunks,
    )
    executor = MockMaxRanker()
    driver.attach(executor=executor, runtime=None)
    driver()
    dm = list(doc.matches)
    assert len(dm) == 2
    assert dm[0].id == '20'
    assert dm[0].score.value == 40
    assert dm[1].id == '30'
    assert dm[1].score.value == 20
    for match in dm:
        # match score is computed w.r.t to doc.id
        assert match.score.ref_id == doc.id
        expected_chunk_matches_length = 2 if keep_source_matches_as_chunks else 0
        assert len(match.chunks) == expected_chunk_matches_length
