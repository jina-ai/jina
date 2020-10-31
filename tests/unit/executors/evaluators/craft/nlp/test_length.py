import numpy as np
import pytest

from jina.executors.evaluators.text.length import TextLengthEvaluator


@pytest.mark.parametrize(
    'doc, gt, expected',
    [
        ('aaa', 'bbb', 0.0),
        ('AbcD', 'fghkl', 1.0),
    ]
)
def test_length_evaluator(doc, gt, expected):
    evaluator = TextLengthEvaluator()
    assert evaluator.evaluate(actual=doc, desired=gt) == expected
    assert evaluator._running_stats._n == 1
    np.testing.assert_almost_equal(evaluator.mean, expected)


def test_cosine_evaluator_average():
    doc_content = ['aaa', 'bbb', 'abc']
    gt_content = ['aaaa', 'ccc', 'ddd']

    evaluator = TextLengthEvaluator()
    assert evaluator.evaluate(actual=doc_content[0], desired=gt_content[0]) == 1.0
    assert evaluator.evaluate(actual=doc_content[1], desired=gt_content[1]) == 0.0
    assert evaluator.evaluate(actual=doc_content[2], desired=gt_content[2]) == 0.0
    assert evaluator._running_stats._n == 3
    np.testing.assert_almost_equal(evaluator.mean, 1.0 / 3)
