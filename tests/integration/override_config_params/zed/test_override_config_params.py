import os

import pytest

from jina import Executor, requests
from jina import Flow, Document

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def flow(request):
    flow_src = request.param
    if flow_src == 'flow-yml':
        return Flow().load_config(os.path.join(cur_dir, 'flow.yml'))
    elif flow_src == 'uses-yml':
        return Flow(return_results=True).add(
            uses=os.path.join(cur_dir, 'default_config.yml'),
            uses_with={'param1': 50, 'param2': 30},
            uses_metas={'workspace': 'different_workspace'},
        )
    elif flow_src == 'class':
        from .executor import Override

        return Flow(return_results=True).add(
            uses=Override,
            uses_with={'param1': 50, 'param2': 30, 'param3': 10},
            uses_metas={'workspace': 'different_workspace', 'name': 'name'},
        )


@pytest.mark.parametrize('flow', ['flow-yml', 'uses-yml', 'class'], indirect=['flow'])
def test_override_config_params(flow):
    with flow:
        resps = flow.search(inputs=[Document()], return_results=True)
    doc = resps[0].docs[0]
    assert doc.tags['param1'] == 50
    assert doc.tags['param2'] == 30
    assert doc.tags['param3'] == 10  # not overriden
    assert doc.tags['name'] == 'name'  # not override
    assert doc.tags['workspace'] == 'different_workspace'


def test_override_config_params_parallel():
    flow = Flow(return_results=True).add(
        uses=os.path.join(cur_dir, 'default_config.yml'),
        uses_with={'param1': 50, 'param2': 30},
        uses_metas={'workspace': 'different_workspace'},
        parallel=2,
    )
    with flow:
        resps = flow.search(inputs=[Document()], return_results=True)
    doc = resps[0].docs[0]
    assert doc.tags['param1'] == 50
    assert doc.tags['param2'] == 30
    assert doc.tags['param3'] == 10  # not overriden
    assert doc.tags['name'] == 'name'  # not override
    assert doc.tags['workspace'] == 'different_workspace'


def test_override_requests():
    class MyExec(Executor):
        @requests
        def foo(self, docs, **kwargs):
            for d in docs:
                d.text = 'foo'

        def bar(self, docs, **kwargs):
            for d in docs:
                d.text = 'bar'

        @requests(on=['/1', '/2'])
        def foobar(self, docs, **kwargs):
            for d in docs:
                d.text = 'foobar'

    # original
    f = Flow().add(uses=MyExec)
    with f:
        req = f.post('/index', Document(), return_results=True)
        assert req[0].docs[0].text == 'foo'

    # change bind to bar()
    f = Flow().add(uses=MyExec, uses_requests={'/index': 'bar'})
    with f:
        req = f.post('/index', Document(), return_results=True)
        assert req[0].docs[0].text == 'bar'

        req = f.post('/1', Document(), return_results=True)
        assert req[0].docs[0].text == 'foobar'

    # change bind to foobar()
    f = Flow().add(uses=MyExec, uses_requests={'/index': 'foobar'})
    with f:
        req = f.post('/index', Document(), return_results=True)
        assert req[0].docs[0].text == 'foobar'

        req = f.post('/index-blah', Document(), return_results=True)
        assert req[0].docs[0].text == 'foo'

    # change default bind to foo()
    f = Flow().add(uses=MyExec, uses_requests={'/default': 'bar'})
    with f:
        req = f.post('/index', Document(), return_results=True)
        assert req[0].docs[0].text == 'bar'
