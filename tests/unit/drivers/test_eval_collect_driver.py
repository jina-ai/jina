from jina.flow import Flow
from jina.proto.jina_pb2 import DocumentProto


def input_fn():
    doc1 = DocumentProto()
    doc2 = DocumentProto()
    # doc1 and doc2 should have the same id
    ev1 = doc1.evaluations.add()
    ev1.value = 1
    ev1.op_name = 'op1'
    ev2 = doc2.evaluations.add()
    ev2.value = 2
    ev2.op_name = 'op2'
    return [doc1, doc2]


def test_collect_evals_driver(mocker):
    def validate(req):
        mock()
        assert len(req.docs) == 2
        # each doc should now have two evaluations
        for d in req.docs:
            assert len(d.evaluations) == 2

    mock = mocker.Mock()
    # simulate two encoders
    flow = (Flow().add(name='a')
            .add(name='b', needs='gateway')
            .join(needs=['a', 'b'], uses='- !CollectEvaluationDriver {}'))
    with flow:
        flow.index(input_fn=input_fn, on_done=validate, callback_on='body')

    mock.assert_called_once()
