import numpy as np

from jina import Document
from jina.drivers.rank import Matches2DocRankDriver
from jina.executors.rankers import Match2DocRanker
from jina.types.sets import DocumentSet


class MockMatches2DocRankDriver(Matches2DocRankDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


class MockAbsoluteLengthRanker(Match2DocRanker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_keys = {'length'}

    def score(self, query_meta, old_match_scores, match_meta):
        new_scores = [
            (match_id, - abs(match_meta[match_id]['length'] - query_meta['length']))
            for match_id, old_score in old_match_scores.items()
        ]

        return np.array(
            new_scores,
            dtype=[(self.COL_MATCH_HASH, np.int64), (self.COL_SCORE, np.float64)],
        )


def create_document_to_score():
    # doc: 1
    # |- matches: (id: 2, parent_id: 1, score.value: 2),
    # |- matches: (id: 3, parent_id: 1, score.value: 3),
    # |- matches: (id: 4, parent_id: 1, score.value: 4),
    # |- matches: (id: 5, parent_id: 1, score.value: 5),
    doc = Document()
    doc.id = '1' * 16
    doc.length = 5
    for match_id, match_score in [(2, 3), (3, 6), (4, 1), (5, 8)]:
        with Document() as match:
            match.id = str(match_id) * 16
            match.length = match_score
            match.score.value = match_score
            doc.matches.append(match)
    return doc


def test_chunk2doc_ranker_driver_mock_exec():
    doc = create_document_to_score()
    driver = MockMatches2DocRankDriver()
    executor = MockAbsoluteLengthRanker()
    driver.attach(executor=executor, runtime=None)
    driver._traverse_apply(DocumentSet([doc, ]))
    assert len(doc.matches) == 4
    assert doc.matches[0].id == '3' * 16
    assert doc.matches[0].score.value == -1
    assert doc.matches[1].id == '2' * 16
    assert doc.matches[1].score.value == -2
    assert doc.matches[2].id == '5' * 16
    assert doc.matches[2].score.value == -3
    assert doc.matches[3].id == '4' * 16
    assert doc.matches[3].score.value == -4
    for match in doc.matches:
        assert match.score.ref_id == doc.id
        assert match.score.op_name == 'MockAbsoluteLengthRanker'
