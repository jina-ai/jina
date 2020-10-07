import pytest

from jina.proto import jina_pb2
from jina.executors.evaluators.precision import PrecisionEvaluator

@pytest.fixture(scope='function')
def jina_pb2_document():
    class JinaPb2DocumentFactory(object):
        def create(self, tags_id):
            document = jina_pb2.Document()
            document.tags['id'] = tags_id
            return document
    return JinaPb2DocumentFactory()


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
def test_precision_evaluator(jina_pb2_document, eval_at, expected):
    matches = [
        jina_pb2_document.create(0),
        jina_pb2_document.create(1),
        jina_pb2_document.create(2),
        jina_pb2_document.create(3),
        jina_pb2_document.create(4),
    ]

    groundtruth = [
        jina_pb2_document.create(1),
        jina_pb2_document.create(0),
        jina_pb2_document.create(20),
        jina_pb2_document.create(30),
        jina_pb2_document.create(40),
    ]

    evaluator = PrecisionEvaluator(eval_at=eval_at, id_tag='id')
    assert evaluator.evaluate(matches=matches, groundtruth=groundtruth) == expected


def test_precision_evaluator_no_groundtruth(jina_pb2_document):
    matches = [
        jina_pb2_document.create(0),
        jina_pb2_document.create(1),
        jina_pb2_document.create(2),
        jina_pb2_document.create(3),
        jina_pb2_document.create(4),
    ]

    groundtruth = []

    evaluator = PrecisionEvaluator(eval_at=2, id_tag='id')
    assert evaluator.evaluate(matches=matches, groundtruth=groundtruth) == 0.0

