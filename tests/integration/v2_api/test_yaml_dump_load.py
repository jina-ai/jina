import os

import pytest

from jina import Executor, requests, Flow, Document


class MyExec(Executor):
    def __init__(self, bar: str, bar2: int = 3, **kwargs):
        super().__init__(**kwargs)
        self.bar = bar
        self.bar2 = bar2

    @requests(on=['/foo', '/foo2'])
    def foo(self, docs, **kwargs):
        print(f'foo: {kwargs}')
        print(self.workspace)
        for d in docs:
            d.text = '/foo'

    @requests
    def bar(self, docs, **kwargs):
        print(f'bar: {kwargs}')
        for d in docs:
            d.text = '/bar'

    def random(self, docs, **kwargs):
        print(f'random: {kwargs}')
        for d in docs:
            d.text = '/random'


y = """
jtype: MyExec
with:
    bar: hello
    bar2: 1
metas:
    name: my-awesomeness
    description: this is an awesome executor
requests:
    /foo_endpoint: foo
    /random_endpoint: random
"""


def test_load_save_yml(tmp_path):
    m = Executor.load_config(y)
    m.save_config(os.path.join(tmp_path, 'a.yml'))

    assert m.bar == 'hello'
    assert m.bar2 == 1
    assert m.metas.name == 'my-awesomeness'
    for k in ('/foo', '/foo2', '/default', '/foo_endpoint', '/random_endpoint'):
        assert k in m.requests


@pytest.mark.parametrize(
    'req_endpoint, doc_text',
    [
        ('/foo', '/foo'),
        ('/foo2', '/foo'),
        ('/foo3', '/bar'),
        ('/foo_endpoint', '/foo'),
        ('/random_endpoint', '/random'),
        ('/bar', '/bar'),
    ],
)
def test_load_yaml_route(mocker, req_endpoint, doc_text):
    f = Flow().add(uses=y)

    mock = mocker.Mock()

    def validate(req):
        mock()
        assert req.docs[0].text == doc_text

    with f:
        f.post(req_endpoint, Document(), on_done=validate)
