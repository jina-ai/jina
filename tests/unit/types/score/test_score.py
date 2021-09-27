import pytest

from jina.excepts import BadNamedScoreType
from jina.proto import jina_pb2
from jina.types.score import NamedScore


def test_named_score():
    score = NamedScore(
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
    from jina.proto.jina_pb2 import NamedScoreProto

    proto = NamedScoreProto()
    proto.op_name = 'operation'
    proto.value = 10.0
    proto.ref_id = '10' * 16
    proto.description = 'score description'
    score = NamedScore(score=proto, copy=copy)

    assert score.op_name == 'operation'
    assert score.value == 10.0
    assert score.ref_id == '10' * 16
    assert score.description == 'score description'


def test_named_score_setters():
    score = NamedScore()
    score.op_name = 'operation'
    score.value = 10.0
    score.ref_id = '10' * 16
    score.description = 'score description'

    assert score.op_name == 'operation'
    assert score.value == 10.0
    assert score.ref_id == '10' * 16
    assert score.description == 'score description'


score_proto_1 = jina_pb2.NamedScoreProto()
score_proto_1.op_name = 'operation1'
score_proto_2 = jina_pb2.NamedScoreProto()
score_proto_2.op_name = 'operation2'


@pytest.mark.parametrize(
    'operands',
    [
        [NamedScore(op_name='operation1'), NamedScore(op_name='operation2')],
        [score_proto_1, score_proto_2],
        [{'op_name': 'operation1'}, {'op_name': 'operation2'}],
    ],
)
def test_named_operands_nested_score(operands):
    score = NamedScore(operands=operands)
    assert len(score.operands) == 2
    for i, operand in enumerate(score.operands):
        assert isinstance(operand, NamedScore)
        assert operand.op_name == f'operation{i + 1}'


def test_named_score_wrong():
    with pytest.raises(BadNamedScoreType):
        NamedScore('wrong_input_type')

    with pytest.raises(AttributeError):
        NamedScore(invalid='hey')

    with pytest.raises(AttributeError):
        NamedScore(op_name=['hey'])

    with pytest.raises(AttributeError):
        NamedScore(operands=['hey'])
