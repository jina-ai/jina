import pytest

from docarray import Document
from docarray.array.chunk import ChunkArray
from docarray.array.match import MatchArray
from docarray.simple import NamedScore


@pytest.mark.parametrize(
    'obj',
    [
        Document(),
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
