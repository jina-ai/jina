import pytest

from jina.executors.evaluators.rank.recall import RecallEvaluator


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
    assert evaluator.evaluate(prediction=matches_ids, groundtruth=groundtruth_ids) == expected
    assert evaluator._num_docs == 1
    assert evaluator._total_sum == expected
    assert evaluator.avg == expected


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
    assert evaluator.evaluate(prediction=matches_ids[0], groundtruth=groundtruth_ids[0]) == expected_first
    assert evaluator.evaluate(prediction=matches_ids[1], groundtruth=groundtruth_ids[1]) == 0.0
    assert evaluator.evaluate(prediction=matches_ids[2], groundtruth=groundtruth_ids[2]) == 0.0
    assert evaluator._num_docs == 3
    assert evaluator._total_sum == expected_first
    assert evaluator.avg == expected_first / 3


def test_recall_evaluator_no_matches():
    matches_ids = []

    groundtruth_ids = [1, 0, 20, 30, 40]

    evaluator = RecallEvaluator(eval_at=2)
    assert evaluator.evaluate(prediction=matches_ids, groundtruth=groundtruth_ids) == 0.0
    assert evaluator._num_docs == 1
    assert evaluator._total_sum == 0.0
    assert evaluator.avg == 0.0
