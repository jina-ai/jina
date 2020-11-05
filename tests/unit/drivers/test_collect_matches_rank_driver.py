import pytest

from jina.drivers.rank import CollectMatches2DocRankDriver
from jina.executors.rankers import Chunk2DocRanker
from jina.proto import jina_pb2


class MockMaxRanker(Chunk2DocRanker):

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return self.get_doc_id(match_idx), match_idx[self.COL_SCORE].max()


class MockMinRanker(Chunk2DocRanker):

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return self.get_doc_id(match_idx), 1. / (1. + match_idx[self.COL_SCORE].min())


class SimpleCollectMatchesRankDriver(CollectMatches2DocRankDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hash2id = lambda x: str(int(x))
        self.id2hash = lambda x: int(x)

    @property
    def exec_fn(self):
        return self._exec_fn


class MockLengthRanker(Chunk2DocRanker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_keys = {'length'}

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return match_idx[0][self.COL_MATCH_PARENT_HASH], match_chunk_meta[match_idx[0][self.COL_MATCH_HASH]]['length']


def create_document_to_score_same_depth_level():
    # doc: 1
    # |  matches: (id: 2, parent_id: 20, score.value: 30, length: 3),
    # |  matches: (id: 3, parent_id: 20, score.value: 40, length: 4),
    # |  matches: (id: 4, parent_id: 30, score.value: 20, length: 2),
    # |  matches: (id: 5, parent_id: 30, score.value: 10, length: 1),

    doc = jina_pb2.Document()
    doc.id = str(1)

    match2 = doc.matches.add()
    match2.id = str(2)
    match2.parent_id = str(20)
    match2.length = 3
    match2.score.ref_id = doc.id
    match2.score.value = 30

    match3 = doc.matches.add()
    match3.id = str(3)
    match3.parent_id = str(20)
    match3.length = 4
    match3.score.ref_id = doc.id
    match3.score.value = 40

    match4 = doc.matches.add()
    match4.id = str(4)
    match4.parent_id = str(30)
    match4.length = 2
    match4.score.ref_id = doc.id
    match4.score.value = 20

    match5 = doc.matches.add()
    match5.id = str(4)
    match5.parent_id = str(30)
    match5.length = 1
    match5.score.ref_id = doc.id
    match5.score.value = 10

    return doc


def test_collect_matches2doc_ranker_driver_mock_ranker():
    doc = create_document_to_score_same_depth_level()
    driver = SimpleCollectMatchesRankDriver()
    executor = MockLengthRanker()
    driver.attach(executor=executor, pea=None)
    driver._traverse_apply([doc, ])
    assert len(doc.matches) == 2
    assert doc.matches[0].id == '20'
    assert doc.matches[0].score.value == 3
    assert doc.matches[1].id == '30'
    assert doc.matches[1].score.value == 1
    for match in doc.matches:
        # match score is computed w.r.t to doc.id
        assert match.score.ref_id == doc.id


test_collect_matches2doc_ranker_driver_mock_ranker()


def test_collect_matches2doc_ranker_driver_min_ranker():
    doc = create_document_to_score_same_depth_level()
    driver = SimpleCollectMatchesRankDriver()
    executor = MockMinRanker()
    driver.attach(executor=executor, pea=None)
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
    driver._traverse_apply([doc, ])
    assert len(doc.matches) == 2
    assert doc.matches[0].id == '30'
    assert doc.matches[0].score.value == pytest.approx((1. / (1. + min_value_30)), 0.0000001)
    assert doc.matches[1].id == '20'
    assert doc.matches[1].score.value == pytest.approx((1. / (1. + min_value_20)), 0.0000001)
    for match in doc.matches:
        # match score is computed w.r.t to doc.id
        assert match.score.ref_id == doc.id


def test_collect_matches2doc_ranker_driver_max_ranker():
    doc = create_document_to_score_same_depth_level()
    driver = SimpleCollectMatchesRankDriver()
    executor = MockMaxRanker()
    driver.attach(executor=executor, pea=None)
    driver._traverse_apply([doc, ])
    assert len(doc.matches) == 2
    assert doc.matches[0].id == '20'
    assert doc.matches[0].score.value == 40
    assert doc.matches[1].id == '30'
    assert doc.matches[1].score.value == 20
    for match in doc.matches:
        # match score is computed w.r.t to doc.id
        assert match.score.ref_id == doc.id
