import pytest

from docarray import Document, Flow


@pytest.mark.parametrize('endpoint', ['foo', 'bar'])
@pytest.mark.parametrize(
    'uses', ['jinaai+sandbox://jina-ai/Hello']
)
def test_sandbox(endpoint, uses):
    with Flow().add(uses=uses) as f:
        da = f.post(
            endpoint,
            [
                Document(text="dog world"),
                Document(text="cat world"),
                Document(id="a", text="elephant world"),
                Document(id="b", text="monkey world"),
            ],
        )
        assert da.texts == [
            'hello dog world',
            'hello cat world',
            'hello elephant world',
            'hello monkey world',
        ]
