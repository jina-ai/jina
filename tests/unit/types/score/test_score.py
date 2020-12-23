import pytest

from jina.types.score import NamedScore


def test_named_score():
    score = NamedScore(op_name='operation',
                       value=10.0,
                       ref_id='10' * 16,
                       description='score description')

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
