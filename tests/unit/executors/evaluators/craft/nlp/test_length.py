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
    assert evaluator.evaluate(predicton=doc, groundtruth=gt) == expected
    assert evaluator._num_docs == 1
    assert evaluator._total_sum == expected
    assert evaluator.avg == expected


def test_cosine_evaluator_average():
    doc_content = ['aaa', 'bbb', 'abc']
    gt_content = ['aaaa', 'ccc', 'ddd']

    evaluator = TextLengthEvaluator()
    assert evaluator.evaluate(predicton=doc_content[0], groundtruth=gt_content[0]) == 1.0
    assert evaluator.evaluate(predicton=doc_content[1], groundtruth=gt_content[1]) == 0.0
    assert evaluator.evaluate(predicton=doc_content[2], groundtruth=gt_content[2]) == 0.0
    assert evaluator._num_docs == 3
    assert evaluator._total_sum == 1.0
    assert evaluator.avg == 1.0 / 3
