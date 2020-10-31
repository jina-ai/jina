import numpy as np
import pytest

from jina.executors.evaluators.embedding.cosine import CosineEvaluator


@pytest.mark.parametrize(
    'doc_embedding, gt_embedding, expected',
    [
        ([0, 1], [0, 1], 0.0),
        ([0, 1], [1, 0], 1.0),
        ([1, 0], [0, 1], 1.0),
        ([1, 0], [1, 0], 0.0),
        ([0, -1], [0, 1], 2.0)  # https://github.com/scipy/scipy/issues/9322
    ]
)
def test_cosine_evaluator(doc_embedding, gt_embedding, expected):
    evaluator = CosineEvaluator()
    assert evaluator.evaluate(actual=doc_embedding, desired=gt_embedding) == expected
    assert evaluator._running_stats._n == 1
    np.testing.assert_almost_equal(evaluator.mean, expected)


def test_cosine_evaluator_average():
    doc_embeddings = [np.array([0, 1]), np.array([1, 0]), np.array([2, 2])]
    gt_embeddings = [np.array([1, 0]), np.array([1, 0]), np.array([4, 4])]

    evaluator = CosineEvaluator()
    assert evaluator.evaluate(actual=doc_embeddings[0], desired=gt_embeddings[0]) == 1.0
    assert evaluator.evaluate(actual=doc_embeddings[1], desired=gt_embeddings[1]) == 0.0
    assert evaluator.evaluate(actual=doc_embeddings[2], desired=gt_embeddings[2]) == 0.0
    assert evaluator._running_stats._n == 3
    np.testing.assert_almost_equal(evaluator.mean, 1.0 / 3)
