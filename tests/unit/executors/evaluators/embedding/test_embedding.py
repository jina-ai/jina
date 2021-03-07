import numpy as np
import pytest

from jina.executors.evaluators.embedding.cosine import CosineEvaluator
from jina.executors.evaluators.embedding.euclidean import EuclideanEvaluator


@pytest.mark.parametrize(
    'embedding1, embedding2, distance',
    [
        ([1, 1, 1], [1, 1, 1], 0),
        ([0, 1], [1, 0], 1),
        ([1, 2, 4, 7, 3], [5, 4, 3, 8, 9], 0.12985245),
    ],
)
def test_euclidean(embedding1, embedding2, distance):
    evaluator = CosineEvaluator()
    res = evaluator.evaluate(actual=np.array(embedding1), desired=np.array(embedding2))
    np.testing.assert_almost_equal(res, distance)


@pytest.mark.parametrize(
    'embedding1, embedding2, distance',
    [
        ([1, 1, 1], [1, 1, 1], 0),
        ([2, 4], [2, 5], 1),
        ([1, 2, 4, 7, 3], [5, 4, 3, 8, 9], 7.61577311),
    ],
)
def test_cosine(embedding1, embedding2, distance):
    evaluator = EuclideanEvaluator()
    res = evaluator.evaluate(actual=np.array(embedding1), desired=np.array(embedding2))
    np.testing.assert_almost_equal(res, distance)
