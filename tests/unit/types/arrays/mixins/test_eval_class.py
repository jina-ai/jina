import numpy as np
import pytest

from jina import DocumentArray, Document


@pytest.mark.parametrize(
    'metric_fn, kwargs',
    [
        ('r_precision', {}),
        ('precision_at_k', {}),
        ('hit_at_k', {}),
        ('average_precision', {}),
        ('reciprocal_rank', {}),
        ('recall_at_k', {'max_rel': 9}),
        ('f1_score_at_k', {'max_rel': 9}),
        ('ndcg_at_k', {}),
    ],
)
def test_eval_mixin_perfect_match(metric_fn, kwargs):
    da = DocumentArray.empty(10)
    da.embeddings = np.random.random([10, 256])
    da.match(da, exclude_self=True)
    r = da.evaluate(da, metric=metric_fn, **kwargs)
    assert isinstance(r, float)
    assert r == 1.0
    for d in da:
        assert d.evaluations[metric_fn].value == 1.0


@pytest.mark.parametrize(
    'metric_fn, kwargs',
    [
        ('r_precision', {}),
        ('precision_at_k', {}),
        ('hit_at_k', {}),
        ('average_precision', {}),
        ('reciprocal_rank', {}),
        ('recall_at_k', {'max_rel': 9}),
        ('f1_score_at_k', {'max_rel': 9}),
        ('ndcg_at_k', {}),
    ],
)
def test_eval_mixin_zero_match(metric_fn, kwargs):
    da1 = DocumentArray.empty(10)
    da1.embeddings = np.random.random([10, 256])
    da1.match(da1, exclude_self=True)

    da2 = DocumentArray.empty(10)
    da2.embeddings = np.random.random([10, 256])
    da2.match(da2, exclude_self=True)

    r = da1.evaluate(da2, metric=metric_fn, **kwargs)
    assert isinstance(r, float)
    assert r == 0.0
    for d in da1:
        d: Document
        assert d.evaluations[metric_fn].value == 0.0
