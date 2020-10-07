import pytest

from jina.executors.evaluators.rank.precision import PrecisionEvaluator


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
def test_precision_evaluator(eval_at, expected):
    matches_ids = [0, 1, 2, 3, 4]

    groundtruth_ids = [1, 0, 20, 30, 40]

    evaluator = PrecisionEvaluator(eval_at=eval_at)
    assert evaluator.evaluate(matches_ids=matches_ids, groundtruth_ids=groundtruth_ids) == expected


def test_precision_evaluator_no_groundtruth():
    matches_ids = [0, 1, 2, 3, 4]

    groundtruth_ids = []

    evaluator = PrecisionEvaluator(eval_at=2)
    assert evaluator.evaluate(matches_ids=matches_ids, groundtruth_ids=groundtruth_ids) == 0.0
