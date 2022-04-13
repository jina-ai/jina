import pytest

from jina import Document, Flow


@pytest.mark.parametrize('endpoint', ['foo', 'bar'])
def test_sandbox(endpoint):
    with Flow().add(uses='jinahub+sandbox://Hello') as f:
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
