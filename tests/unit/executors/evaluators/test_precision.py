from jina.proto import jina_pb2
from jina.executors.evaluators.precision import PrecisionEvaluator


def test_precision_evaluator():
    def matches():
        match0 = jina_pb2.Document()
        match0.tags['id'] = 0
        match1 = jina_pb2.Document()
        match1.tags['id'] = 1
        match2 = jina_pb2.Document()
        match2.tags['id'] = 2
        match3 = jina_pb2.Document()
        match3.tags['id'] = 3
        match4 = jina_pb2.Document()
        match4.tags['id'] = 4
        return [match0, match1, match2, match3, match4]

    def groundtruth():
        match0 = jina_pb2.Document()
        match0.tags['id'] = 1
        match1 = jina_pb2.Document()
        match1.tags['id'] = 0
        match2 = jina_pb2.Document()
        match2.tags['id'] = 20
        match3 = jina_pb2.Document()
        match3.tags['id'] = 30
        match4 = jina_pb2.Document()
        match4.tags['id'] = 40
        return [match0, match1, match2, match3, match4]

    evaluator = PrecisionEvaluator(eval_at=2, id_tag='id')
    assert evaluator.evaluate(matches=matches(), groundtruth=groundtruth()) == 1.0

    evaluator = PrecisionEvaluator(eval_at=4, id_tag='id')
    assert evaluator.evaluate(matches=matches(), groundtruth=groundtruth()) == 0.5

    evaluator = PrecisionEvaluator(eval_at=5, id_tag='id')
    assert evaluator.evaluate(matches=matches(), groundtruth=groundtruth()) == 0.4

    evaluator = PrecisionEvaluator(eval_at=100, id_tag='id')
    assert evaluator.evaluate(matches=matches(), groundtruth=groundtruth()) == 0.4


def test_precision_evaluator_no_groundtruth():
    def matches():
        match0 = jina_pb2.Document()
        match0.tags['id'] = 0
        match1 = jina_pb2.Document()
        match1.tags['id'] = 1
        match2 = jina_pb2.Document()
        match2.tags['id'] = 2
        match3 = jina_pb2.Document()
        match3.tags['id'] = 3
        match4 = jina_pb2.Document()
        match4.tags['id'] = 4
        return [match0, match1, match2, match3, match4]

    def groundtruth():
        return []

    evaluator = PrecisionEvaluator(eval_at=2, id_tag='id')
    assert evaluator.evaluate(matches=matches(), groundtruth=groundtruth()) == 0.0


def test_precision_evaluator_eval_at_0():
    def matches():
        match0 = jina_pb2.Document()
        match0.tags['id'] = 0
        match1 = jina_pb2.Document()
        match1.tags['id'] = 1
        match2 = jina_pb2.Document()
        match2.tags['id'] = 2
        match3 = jina_pb2.Document()
        match3.tags['id'] = 3
        match4 = jina_pb2.Document()
        match4.tags['id'] = 4
        return [match0, match1, match2, match3, match4]

    def groundtruth():
        match0 = jina_pb2.Document()
        match0.tags['id'] = 1
        match1 = jina_pb2.Document()
        match1.tags['id'] = 0
        match2 = jina_pb2.Document()
        match2.tags['id'] = 20
        match3 = jina_pb2.Document()
        match3.tags['id'] = 30
        match4 = jina_pb2.Document()
        match4.tags['id'] = 40
        return [match0, match1, match2, match3, match4]

    evaluator = PrecisionEvaluator(eval_at=0, id_tag='id')
    assert evaluator.evaluate(matches=matches(), groundtruth=groundtruth()) == 0.0
