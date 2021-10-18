import pytest

from jina import Document, DocumentArray

from jina import Document, DocumentArray


@pytest.mark.parametrize(
    'eval_at, expected',
    [(None, 0.4), (0, 0.0), (2, 1.0), (4, 0.5), (5, 0.4), (100, 0.4)],
)
def test_ranking_evaluator_precision(eval_at, expected):
    matches = DocumentArray([Document(tags={'id': i}) for i in range(5)])
    matches_gt = DocumentArray(
        [
            Document(tags={'id': 1}),
            Document(tags={'id': 0}),
            Document(tags={'id': 20}),
            Document(tags={'id': 30}),
            Document(tags={'id': 40}),
        ]
    )
    query = Document()
    query.matches = matches
    gt = Document()
    gt.matches = matches_gt

    result = DocumentArray([query]).evaluate(
        groundtruth=DocumentArray([gt]), metrics='precision', eval_at=eval_at
    )
    print(f' query evals {query.evaluations._pb_body}')
    name = f'precision@{eval_at}' if eval_at is not None else 'precision'
    assert query.evaluations[name].value == pytest.approx(expected, 0.0001)
    assert result == pytest.approx(expected, 0.0001)


@pytest.mark.parametrize(
    'eval_at, expected',
    [(None, 0.4), (0, 0.0), (2, 1.0), (4, 0.5), (5, 0.4), (100, 0.4)],
)
def test_ranking_evaluator_precision_chunks(eval_at, expected):
    matches = DocumentArray([Document(tags={'id': i}) for i in range(5)])
    matches_gt = DocumentArray(
        [
            Document(tags={'id': 1}),
            Document(tags={'id': 0}),
            Document(tags={'id': 20}),
            Document(tags={'id': 30}),
            Document(tags={'id': 40}),
        ]
    )
    query = Document()
    query_chunk = Document()
    query_chunk.matches = matches
    query.chunks = DocumentArray([query_chunk])
    gt = Document()
    gt_chunk = Document()
    gt_chunk.matches = matches_gt
    gt.chunks = DocumentArray([gt_chunk])

    result = DocumentArray([query]).evaluate(
        groundtruth=DocumentArray([gt]),
        metrics='precision',
        eval_at=eval_at,
        traversal_paths=['c'],
    )
    name = f'precision@{eval_at}' if eval_at is not None else 'precision'
    assert query.chunks[0].evaluations[name].value == pytest.approx(expected, 0.0001)
    assert result == pytest.approx(expected, 0.0001)


@pytest.mark.parametrize(
    'eval_at',
    [0, 1, 3, 5, 10],
)
@pytest.mark.parametrize(
    'metric', ['precision', 'recall', 'average_precision', 'reciprocal_rank', 'fscore']
)
def test_ranking_evaluator_metrics_available(eval_at, metric):
    matches = DocumentArray([Document(tags={'id': i}) for i in range(5)])
    matches_gt = DocumentArray(
        [
            Document(tags={'id': 1}),
            Document(tags={'id': 0}),
            Document(tags={'id': 20}),
            Document(tags={'id': 30}),
            Document(tags={'id': 40}),
        ]
    )
    query = Document()
    query.matches = matches
    gt = Document()
    gt.matches = matches_gt

    name = f'{metric}@{eval_at}' if eval_at is not None else metric
    result = DocumentArray([query]).evaluate(
        groundtruth=DocumentArray([gt]), metrics=metric, eval_at=eval_at, beta=0.1
    )
    assert name in query.evaluations
    print(f' query evaluations {query.evaluations}')


@pytest.mark.parametrize('power_relevance, expected', [(False, 0.278), (True, 0.209)])
def test_ranking_evaluator_ndcg(power_relevance, expected):
    matches = DocumentArray(
        [
            Document(tags={'id': 1}, scores={'relevance': 0.0}),
            Document(tags={'id': 3}, scores={'relevance': 0.1}),
            Document(tags={'id': 4}, scores={'relevance': 0.2}),
            Document(tags={'id': 2}, scores={'relevance': 0.3}),
        ]
    )
    matches_gt = DocumentArray(
        [
            Document(tags={'id': 1}, scores={'relevance': 0.8}),
            Document(tags={'id': 3}, scores={'relevance': 0.4}),
            Document(tags={'id': 4}, scores={'relevance': 0.1}),
            Document(tags={'id': 2}, scores={'relevance': 0.0}),
        ]
    )
    query = Document()
    query.matches = matches
    gt = Document()
    gt.matches = matches_gt

    result = DocumentArray([query]).evaluate(
        groundtruth=DocumentArray([gt]),
        metrics='ndcg',
        eval_at=3,
        attribute_fields=['tags__id', 'scores__values__relevance__value'],
        power_relevance=power_relevance,
        is_relevance_score=True,
    )
    print(f' query evaluations {query.evaluations}')
