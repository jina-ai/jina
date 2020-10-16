from jina.flow import Flow
from jina.proto.jina_pb2 import Document


def input_fn():
    doc1 = Document()
    doc2 = Document()
    ev1 = doc1.evaluations.add()
    ev1.value = 1
    ev1.op_name = 'op1'
    ev2 = doc2.evaluations.add()
    ev2.value = 2
    ev2.op_name = 'op2'
    return [doc1, doc2]


def test_collect_evals_driver():
    def validate(req):
        assert len(req.docs) == 2
        # each doc should now have two evaluations
        for d in req.docs:
            assert len(d.evaluations) == 2

    # simulate two encoders
    flow = (Flow().add(name='a')
            .add(name='b', needs='gateway')
            .join(needs=['a', 'b'], uses='- !CollectEvaluationDriver {}'))

    with flow:
        flow.index(input_fn=input_fn, output_fn=validate, callback_on_body=True)
