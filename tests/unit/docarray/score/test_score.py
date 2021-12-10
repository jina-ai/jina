import pytest

from jina.excepts import BadNamedScoreType
from jina.docarray.proto import docarray_pb2
from jina.docarray.simple import ScoreView


def test_named_score():
    score = ScoreView(
        op_name='operation',
        value=10.0,
        ref_id='10' * 16,
        description='score description',
    )

    assert score.op_name == 'operation'
    assert score.value == 10.0
    assert score.ref_id == '10' * 16
    assert score.description == 'score description'


@pytest.mark.parametrize('copy', [True, False])
def test_named_score_from_proto(copy):

    proto = docarray_pb2.NamedScoreProto()
    proto.op_name = 'operation'
    proto.value = 10.0
    proto.ref_id = '10' * 16
    proto.description = 'score description'
    score = ScoreView(score=proto, copy=copy)

    assert score.op_name == 'operation'
    assert score.value == 10.0
    assert score.ref_id == '10' * 16
    assert score.description == 'score description'


def test_named_score_setters():
    score = ScoreView()
    score.op_name = 'operation'
    score.value = 10.0
    score.ref_id = '10' * 16
    score.description = 'score description'

    assert score.op_name == 'operation'
    assert score.value == 10.0
    assert score.ref_id == '10' * 16
    assert score.description == 'score description'


score_proto_1 = docarray_pb2.NamedScoreProto()
score_proto_1.op_name = 'operation1'
score_proto_2 = docarray_pb2.NamedScoreProto()
score_proto_2.op_name = 'operation2'


@pytest.mark.parametrize(
    'operands',
    [
        [ScoreView(op_name='operation1'), ScoreView(op_name='operation2')],
        [score_proto_1, score_proto_2],
        [{'op_name': 'operation1'}, {'op_name': 'operation2'}],
    ],
)
def test_named_operands_nested_score(operands):
    score = ScoreView(operands=operands)
    assert len(score.operands) == 2
    for i, operand in enumerate(score.operands):
        assert isinstance(operand, ScoreView)
        assert operand.op_name == f'operation{i + 1}'


def test_named_score_wrong():
    with pytest.raises(BadNamedScoreType):
        ScoreView('wrong_input_type')

    with pytest.raises(AttributeError):
        ScoreView(invalid='hey')

    with pytest.raises(AttributeError):
        ScoreView(op_name=['hey'])

    with pytest.raises(AttributeError):
        ScoreView(operands=['hey'])
