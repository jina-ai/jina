import os
import pytest

from jina import Flow, Document

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def flow(request):
    flow_src = request.param
    if flow_src == 'yml':
        return Flow().load_config(os.path.join(cur_dir, 'flow.yml'))
    elif flow_src == 'python':
        return Flow(return_results=True).add(
            uses=os.path.join(cur_dir, 'default_config.yml'),
            override_with={'param1': 50, 'param2': 30},
            override_metas={'workspace': 'different_workspace'},
        )


@pytest.mark.parametrize('flow', ['yml', 'python'], indirect=['flow'])
def test_override_config_params(flow):
    with flow:
        resps = flow.search(inputs=[Document()], return_results=True)
    doc = resps[0].docs[0]
    assert doc.tags['param1'] == 50
    assert doc.tags['param2'] == 30
    assert doc.tags['param3'] == 10  # not overriden
    assert doc.tags['name'] == 'name'  # not override
    assert doc.tags['workspace'] == 'different_workspace'
