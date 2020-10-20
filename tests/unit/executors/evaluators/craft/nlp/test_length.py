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
    assert evaluator.evaluate(doc_content=doc, groundtruth_content=gt) == expected
    assert evaluator.num_documents == 1
    assert evaluator.sum == expected
    assert evaluator.avg == expected


def test_cosine_evaluator_average():
    doc_content = ['aaa', 'bbb', 'abc']
    gt_content = ['aaaa', 'ccc', 'ddd']

    evaluator = TextLengthEvaluator()
    assert evaluator.evaluate(doc_content=doc_content[0], groundtruth_content=gt_content[0]) == 1.0
    assert evaluator.evaluate(doc_content=doc_content[1], groundtruth_content=gt_content[1]) == 0.0
    assert evaluator.evaluate(doc_content=doc_content[2], groundtruth_content=gt_content[2]) == 0.0
    assert evaluator.num_documents == 3
    assert evaluator.sum == 1.0
    assert evaluator.avg == 1.0 / 3
