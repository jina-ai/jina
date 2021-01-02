import numpy as np
import pytest

from jina.executors.evaluators.rank.precision import PrecisionEvaluator


@pytest.mark.parametrize(
    'eval_at, expected',
    [
        (None, 0.4),
        (0, 0.0),
        (2, 1.0),
        (4, 0.5),
        (5, 0.4),
        (100, 0.4)
    ]
)
def test_precision_evaluator(eval_at, expected):
    matches_ids = [0, 1, 2, 3, 4]

    desired_ids = [1, 0, 20, 30, 40]

    evaluator = PrecisionEvaluator(eval_at=eval_at)
    assert evaluator.evaluate(actual=matches_ids, desired=desired_ids) == expected
    np.testing.assert_almost_equal(evaluator.mean, expected)


@pytest.mark.parametrize(
    'eval_at, expected_first',
    [
        (None, 0.4),
        (0, 0.0),
        (2, 1.0),
        (4, 0.5),
        (5, 0.4),
        (100, 0.4)
    ]
)
def test_precision_evaluator_average(eval_at, expected_first):
    matches_ids = [[0, 1, 2, 3, 4], [-1, -1, -1, -1, -1], [-1, -1, -1, -1, -1]]

    desired_ids = [[1, 0, 20, 30, 40], [1, 0, 20, 30, 40], [1, 0, 20, 30, 40]]

    evaluator = PrecisionEvaluator(eval_at=eval_at)
    assert evaluator.evaluate(actual=matches_ids[0], desired=desired_ids[0]) == expected_first
    assert evaluator.evaluate(actual=matches_ids[1], desired=desired_ids[1]) == 0.0
    assert evaluator.evaluate(actual=matches_ids[2], desired=desired_ids[2]) == 0.0
    assert evaluator._running_stats._n == 3
    np.testing.assert_almost_equal(evaluator.mean, expected_first / 3)


def test_precision_evaluator_no_groundtruth():
    matches_ids = [0, 1, 2, 3, 4]

    desired_ids = []

    evaluator = PrecisionEvaluator(eval_at=2)
    assert evaluator.evaluate(actual=matches_ids, desired=desired_ids) == 0.0
    assert evaluator._running_stats._n == 1
    np.testing.assert_almost_equal(evaluator.mean, 0.0)
