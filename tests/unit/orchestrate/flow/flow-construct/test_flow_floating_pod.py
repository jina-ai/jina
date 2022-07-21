import pytest

from jina import Document, Executor, Flow, requests


@pytest.mark.parametrize('floating, expect_str', [(True, 'world'), (False, 'hello')])
def test_floating_pod(floating, expect_str):
    class MyFloatingExecutor(Executor):
        @requests
        async def add_text(self, docs, **kwargs):
            docs[0].text = 'hello'

    f = (
        Flow()
            .add(replicas=3, name='a1')
            .add(name='a2', floating=floating, uses=MyFloatingExecutor)
            .add(name='a3')
            .add(floating=floating, uses=MyFloatingExecutor)
    )

    with f:
        da = f.post('/', Document(text='world'))
        assert da[0].text == expect_str
