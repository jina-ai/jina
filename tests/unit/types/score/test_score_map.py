import pytest

import numpy as np

from jina.types.score.map import NamedScoreMapping
from jina.types.score import NamedScore


def test_mapped_named_score():
    scores = NamedScoreMapping()

    scores['operation'].op_name = 'operation'
    scores['operation'].value = 10.0
    scores['operation'].ref_id = '10' * 16
    scores['operation'].description = 'score description'

    scores['operation2'].op_name = 'operation2'
    scores['operation2'].value = 20.0
    scores['operation2'].ref_id = '20' * 16
    scores['operation2'].description = 'score2 description'

    assert len(scores) == 2

    assert 'operation' in scores._pb_body.values
    assert 'operation2' in scores._pb_body.values
    assert 'operation' in scores
    assert 'operation2' in scores

    assert scores['operation'].op_name == 'operation'
    assert scores['operation'].value == 10.0
    assert scores['operation'].ref_id == '10' * 16
    assert scores['operation'].description == 'score description'

    assert scores['operation2'].op_name == 'operation2'
    assert scores['operation2'].value == 20.0
    assert scores['operation2'].ref_id == '20' * 16
    assert scores['operation2'].description == 'score2 description'


def test_mapped_named_score_from_proto():
    scores = NamedScoreMapping()
    scores['operation'].op_name = 'operation'
    scores['operation'].value = 10.0
    scores['operation'].ref_id = '10' * 16
    scores['operation'].description = 'score description'

    scores['operation2'].op_name = 'operation2'
    scores['operation2'].value = 20.0
    scores['operation2'].ref_id = '20' * 16
    scores['operation2'].description = 'score2 description'

    assert 'operation' in scores._pb_body.values
    assert 'operation2' in scores._pb_body.values
    assert 'operation' in scores
    assert 'operation2' in scores

    scores2 = NamedScoreMapping(scores.proto)

    assert 'operation' in scores2._pb_body.values
    assert 'operation2' in scores2._pb_body.values
    assert 'operation' in scores2
    assert 'operation2' in scores2
    assert scores2['operation'].op_name == 'operation'
    assert scores2['operation'].value == 10.0
    assert scores2['operation'].ref_id == '10' * 16
    assert scores2['operation'].description == 'score description'

    assert scores2['operation2'].op_name == 'operation2'
    assert scores2['operation2'].value == 20.0
    assert scores2['operation2'].ref_id == '20' * 16
    assert scores2['operation2'].description == 'score2 description'


@pytest.mark.parametrize(
    'value',
    [5, 5.0, np.int(5), np.float(5.0), NamedScore(value=5), NamedScore(value=5).proto],
)
def test_mapped_set_item(value):
    scores = NamedScoreMapping()
    scores['operation'] = value
    assert scores['operation'].value == 5


@pytest.mark.parametrize(
    'value',
    [
        NamedScore(value=5, op_name='op', description='desc'),
        NamedScore(value=5, op_name='op', description='desc').proto,
    ],
)
def test_mapped_set_item_from_named_score(value):
    scores = NamedScoreMapping()
    scores['operation'] = value
    assert scores['operation'].value == 5
    assert scores['operation'].op_name == 'op'
    assert scores['operation'].description == 'desc'


def test_mapped_named_score_delete():
    scores = NamedScoreMapping()
    scores['operation'].op_name = 'operation'
    scores['operation'].value = 10.0
    scores['operation'].ref_id = '10' * 16
    scores['operation'].description = 'score description'

    scores['operation2'].op_name = 'operation2'
    scores['operation2'].value = 20.0
    scores['operation2'].ref_id = '20' * 16
    scores['operation2'].description = 'score2 description'
    assert len(scores) == 2

    assert 'operation' in scores._pb_body.values
    assert 'operation2' in scores._pb_body.values
    assert 'operation' in scores
    assert 'operation2' in scores
    del scores['operation']
    assert len(scores) == 1
    assert 'operation' not in scores._pb_body.values
    assert 'operation2' in scores._pb_body.values
    assert 'operation' not in scores
    assert 'operation2' in scores
    del scores['operation2']
    assert len(scores) == 0
    assert 'operation2' not in scores._pb_body.values
    assert 'operation2' not in scores
    with pytest.raises(KeyError):
        del scores['operation']


def test_mapped_named_score_iterate():
    scores = NamedScoreMapping()
    scores['operation'].op_name = 'operation'
    scores['operation'].value = 10.0
    scores['operation'].ref_id = '10' * 16
    scores['operation'].description = 'score description'

    scores['operation2'].op_name = 'operation2'
    scores['operation2'].value = 20.0
    scores['operation2'].ref_id = '20' * 16
    scores['operation2'].description = 'score2 description'

    ks = []
    vs = []
    for i, (k, v) in enumerate(scores.items()):
        ks.append(k)
        vs.append(v.value)

    assert set(ks) == {'operation', 'operation2'}
    assert set(vs) == {10.0, 20.0}

    lscores = list(scores.items())
    assert len(lscores) == 2
    assert set(map(lambda s: s[0], lscores)) == {'operation', 'operation2'}
    assert set(map(lambda s: s[1].op_name, lscores)) == {'operation', 'operation2'}
    assert set(map(lambda s: s[1].value, lscores)) == {10.0, 20.0}
