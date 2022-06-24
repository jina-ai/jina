import pytest

from jina import Document, Executor, Flow, requests


class MyExecutor(Executor):
    @requests
    async def add_text(self, docs, **kwargs):
        docs[0].text = 'hello'


@pytest.mark.parametrize('floating, expect_str', [(True, 'world'), (False, 'hello')])
def test_floating_pod(floating, expect_str):
    f = (
        Flow()
        .add(replicas=3, name='a1')
        .add(name='a2', floating=floating, uses=MyExecutor)
        .add(name='a3')
        .add(floating=floating, uses=MyExecutor)
    )

    with f:
        da = f.post('/', Document(text='world'))
        assert da[0].text == expect_str
