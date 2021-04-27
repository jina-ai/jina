import pytest

from typing import List, Dict
from jina.executors.rankers import Match2DocRanker
from jina.executors.decorators import batching, single
from jina import Document
from jina.types.arrays import DocumentArray
from jina.types.score import NamedScore
from jina.flow import Flow
from tests import validate_callback


class DummyRankerBatching(Match2DocRanker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.match_required_keys = ['tags__dummy_score']

    @batching(batch_size=3, slice_nargs=3)
    def score(
        self,
        old_match_scores: List[Dict],
        queries_metas: List[Dict],
        matches_metas: List[List[Dict]],
    ) -> List[List[float]]:
        return [
            [m['tags__dummy_score'] for m in match_meta] for match_meta in matches_metas
        ]


class DummyRankerSingle(Match2DocRanker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.match_required_keys = ['tags__dummy_score']

    @single(slice_nargs=3, flatten_output=False)
    def score(self, old_match_scores, query_metas, match_meta) -> List[List[float]]:
        return [m['tags__dummy_score'] for m in match_meta]


@pytest.mark.parametrize('ranker', [DummyRankerSingle(), DummyRankerBatching()])
def test_match2docranker_batching(ranker):
    NUM_DOCS_QUERIES = 15
    NUM_MATCHES = 10

    old_matches_scores = []
    queries_metas = []
    matches_metas = []
    queries = DocumentArray([])
    for i in range(NUM_DOCS_QUERIES):
        old_match_scores = []
        match_metas = []
        query = Document(id=f'query-{i}')
        for j in range(NUM_MATCHES):
            m = Document(id=f'match-{i}-{j}', tags={'dummy_score': j})
            query.matches.append(m)
            old_match_scores.append(0)
            match_metas.append(m.get_attrs('tags__dummy_score'))
        queries.append(query)
        old_matches_scores.append(old_match_scores)
        queries_metas.append(None)
        matches_metas.append(match_metas)

    queries_scores = ranker.score(old_matches_scores, queries_metas, matches_metas)
    assert len(queries_scores) == NUM_DOCS_QUERIES

    for i, (query, matches_scores) in enumerate(zip(queries, queries_scores)):
        assert len(matches_scores) == NUM_MATCHES
        for j, (match, score) in enumerate(zip(query.matches, matches_scores)):
            match.score = NamedScore(value=j)
            assert score == j

        query.matches.sort(key=lambda x: x.score.value, reverse=True)

        for j, match in enumerate(query.matches, 1):
            assert match.id == f'match-{i}-{NUM_MATCHES - j}'
            assert match.score.value == NUM_MATCHES - j


@pytest.mark.parametrize('ranker', ['!DummyRankerSingle', '!DummyRankerBatching'])
def test_match2docranker_batching_flow(ranker, mocker):
    NUM_DOCS_QUERIES = 15
    NUM_MATCHES = 10
    queries = DocumentArray([])
    for i in range(NUM_DOCS_QUERIES):
        query = Document(id=f'query-{i}')
        for j in range(NUM_MATCHES):
            m = Document(id=f'match-{i}-{j}', tags={'dummy_score': j})
            query.matches.append(m)
        queries.append(query)

    def validate_response(resp):
        assert len(resp.search.docs) == NUM_DOCS_QUERIES
        for i, query in enumerate(resp.search.docs):
            for j, match in enumerate(query.matches, 1):
                assert match.id == f'match-{i}-{NUM_MATCHES - j}'
                assert match.score.value == NUM_MATCHES - j

    mock = mocker.Mock()

    with Flow().add(name='ranker', uses=ranker) as f:
        f.search(inputs=queries, on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate_response)
