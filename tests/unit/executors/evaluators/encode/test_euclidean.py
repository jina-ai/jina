from math import sqrt

import numpy as np
import pytest

from jina.executors.evaluators.embedding.euclidean import EuclideanEvaluator


@pytest.mark.parametrize(
    'doc_embedding, gt_embedding, expected',
    [
        ([0, 0], [0, 0], 0.0),
        ([0, 0], [0, 1], 1.0),
        ([0, 0], [1, 0], 1.0),
        ([0, 0], [1, 1], sqrt(2.0)),
        ([0, 1], [0, 0], 1.0),
        ([0, 1], [0, 1], 0.0),
        ([0, 1], [1, 0], sqrt(2.0)),
        ([0, 1], [1, 1], 1.0),
        ([1, 0], [0, 0], 1.0),
        ([1, 0], [0, 1], sqrt(2.0)),
        ([1, 0], [1, 0], 0.0),
        ([1, 0], [1, 1], 1.0),
        ([1, 1], [0, 0], sqrt(2.0)),
        ([1, 1], [0, 1], 1.0),
        ([1, 1], [1, 0], 1.0),
        ([1, 1], [1, 1], 0.0),
    ]
)
def test_euclidean_evaluator(doc_embedding, gt_embedding, expected):
    evaluator = EuclideanEvaluator()
    assert evaluator.evaluate(actual=doc_embedding, desired=gt_embedding) == expected
    assert evaluator._running_stats._n == 1
    np.testing.assert_almost_equal(evaluator.mean, expected)


def test_euclidean_evaluator_average():
    doc_embeddings = [np.array([0, 1]), np.array([1, 0]), np.array([2, 2])]
    gt_embeddings = [np.array([0, 2]), np.array([1, 0]), np.array([2, 4])]

    evaluator = EuclideanEvaluator()
    assert evaluator.evaluate(actual=doc_embeddings[0], desired=gt_embeddings[0]) == 1.0
    assert evaluator.evaluate(actual=doc_embeddings[1], desired=gt_embeddings[1]) == 0.0
    assert evaluator.evaluate(actual=doc_embeddings[2], desired=gt_embeddings[2]) == 2.0
    assert evaluator._running_stats._n == 3
    np.testing.assert_almost_equal(evaluator.mean, 3.0 / 3)
