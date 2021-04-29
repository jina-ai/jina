import numpy as np
import pytest

from jina import Document, Request, QueryLang, NdArray
from jina.types.score import NamedScore
from jina.types.arrays import ChunkArray
from jina.types.arrays.match import MatchArray


@pytest.mark.parametrize(
    'obj',
    [
        Document(),
        Request(),
        QueryLang(),
        NamedScore(),
        NdArray(),
        MatchArray([Document()], Document()),
        ChunkArray([Document()], Document()),
    ],
)
def test_builtin_str_repr_no_content(obj):
    print(obj)
    print(f'{obj!r}')


@pytest.mark.parametrize(
    'obj',
    [
        Document(content='123', chunks=[Document(content='abc')]),
        QueryLang(
            {
                'name': 'FilterQL',
                'priority': 1,
                'parameters': {
                    'lookups': {'tags__label': 'label2'},
                    'traversal_paths': ['r'],
                },
            }
        ),
        NamedScore(
            op_name='operation',
            value=10.0,
            ref_id='10' * 16,
            description='score description',
        ),
        NdArray(np.random.random([3, 5])),
    ],
)
def test_builtin_str_repr_has_content(obj):
    print(obj)
    print(f'{obj!r}')
