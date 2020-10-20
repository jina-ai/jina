import pytest
import numpy as np
from math import sqrt
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
    assert evaluator.evaluate(prediction=doc_embedding, groundtruth=gt_embedding) == expected
    assert evaluator.num_documents == 1
    assert evaluator.sum == expected
    assert evaluator.avg == expected


def test_euclidean_evaluator_average():
    doc_embeddings = [np.array([0, 1]), np.array([1, 0]), np.array([2, 2])]
    gt_embeddings = [np.array([0, 2]), np.array([1, 0]), np.array([2, 4])]

    evaluator = EuclideanEvaluator()
    assert evaluator.evaluate(prediction=doc_embeddings[0], groundtruth=gt_embeddings[0]) == 1.0
    assert evaluator.evaluate(prediction=doc_embeddings[1], groundtruth=gt_embeddings[1]) == 0.0
    assert evaluator.evaluate(prediction=doc_embeddings[2], groundtruth=gt_embeddings[2]) == 2.0
    assert evaluator.num_documents == 3
    assert evaluator.sum == 3.0
    assert evaluator.avg == 3.0 / 3
