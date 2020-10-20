import pytest
import numpy as np

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
    assert evaluator.evaluate(prediction=doc_embedding, groundtruth=gt_embedding) == expected
    assert evaluator.num_documents == 1
    assert evaluator.sum == expected
    assert evaluator.avg == expected


def test_cosine_evaluator_average():
    doc_embeddings = [np.array([0, 1]), np.array([1, 0]), np.array([2, 2])]
    gt_embeddings = [np.array([1, 0]), np.array([1, 0]), np.array([4, 4])]

    evaluator = CosineEvaluator()
    assert evaluator.evaluate(prediction=doc_embeddings[0], groundtruth=gt_embeddings[0]) == 1.0
    assert evaluator.evaluate(prediction=doc_embeddings[1], groundtruth=gt_embeddings[1]) == 0.0
    assert evaluator.evaluate(prediction=doc_embeddings[2], groundtruth=gt_embeddings[2]) == 0.0
    assert evaluator.num_documents == 3
    assert evaluator.sum == 1.0
    assert evaluator.avg == 1.0 / 3
