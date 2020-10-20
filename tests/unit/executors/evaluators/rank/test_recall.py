import pytest

from jina.executors.evaluators.rank.recall import RecallEvaluator
import numpy as np

@pytest.mark.parametrize(
    'eval_at, expected',
    [
        (0, 0.0),
        (2, 1.0),
        (4, 0.5),
        (5, 0.4),
        (100, 0.4)
    ]
)
def test_recall_evaluator(eval_at, expected):
    matches_ids = [0, 1, 2, 3, 4]

    groundtruth_ids = [1, 0, 20, 30, 40]

    evaluator = RecallEvaluator(eval_at=eval_at)
    assert evaluator.evaluate(actual=matches_ids, desired=groundtruth_ids) == expected
    assert evaluator._running_stats._n == 1
    np.testing.assert_almost_equal(evaluator.mean, expected)


@pytest.mark.parametrize(
    'eval_at, expected_first',
    [
        (0, 0.0),
        (2, 1.0),
        (4, 0.5),
        (5, 0.4),
        (100, 0.4)
    ]
)
def test_recall_evaluator_average(eval_at, expected_first):
    matches_ids = [[0, 1, 2, 3, 4], [0, 1, 2, 3, 4], [0, 1, 2, 3, 4]]

    groundtruth_ids = [[1, 0, 20, 30, 40], [-1, -1, -1, -1, -1],  [-1, -1, -1, -1, -1]]

    evaluator = RecallEvaluator(eval_at=eval_at)
    assert evaluator.evaluate(actual=matches_ids[0], desired=groundtruth_ids[0]) == expected_first
    assert evaluator.evaluate(actual=matches_ids[1], desired=groundtruth_ids[1]) == 0.0
    assert evaluator.evaluate(actual=matches_ids[2], desired=groundtruth_ids[2]) == 0.0
    assert evaluator._running_stats._n == 3
    np.testing.assert_almost_equal(evaluator.mean, expected_first / 3)


def test_recall_evaluator_no_matches():
    matches_ids = []

    groundtruth_ids = [1, 0, 20, 30, 40]

    evaluator = RecallEvaluator(eval_at=2)
    assert evaluator.evaluate(actual=matches_ids, desired=groundtruth_ids) == 0.0
    assert evaluator._running_stats._n == 1
    np.testing.assert_almost_equal(evaluator.mean, 0.0)
