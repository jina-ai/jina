import pytest

from jina import Document
from jina.types.arrays.chunk import ChunkArray
from jina.types.arrays.match import MatchArray
from jina.types.request import Request
from jina.types.score import NamedScore


@pytest.mark.parametrize(
    'obj',
    [
        Document(),
        Request(),
        NamedScore(),
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
        NamedScore(
            op_name='operation',
            value=10.0,
            ref_id='10' * 16,
            description='score description',
        ),
    ],
)
def test_builtin_str_repr_has_content(obj):
    print(obj)
    print(f'{obj!r}')
