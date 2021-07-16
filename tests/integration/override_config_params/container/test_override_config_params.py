import os
import time
import pytest

from jina import Flow, Document

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def docker_image():
    docker_file = os.path.join(cur_dir, 'Dockerfile')
    os.system(f"docker build -f {docker_file} -t override-config-test {cur_dir}")
    time.sleep(3)
    yield
    os.system(f"docker rmi $(docker images | grep 'override-config-test')")


@pytest.fixture()
def flow(request):
    flow_src = request.param
    if flow_src == 'yml':
        return Flow().load_config(os.path.join(cur_dir, 'flow.yml'))
    elif flow_src == 'python':
        return Flow().add(
            uses='docker://override-config-test',
            uses_with={'param1': 50, 'param2': 30},
            uses_metas={'workspace': 'different_workspace'},
        )


@pytest.mark.parametrize('flow', ['yml', 'python'], indirect=['flow'])
def test_override_config_params(docker_image, flow):
    with flow:
        resps = flow.search(inputs=[Document()], return_results=True)
    doc = resps[0].docs[0]
    assert doc.tags['param1'] == 50
    assert doc.tags['param2'] == 30
    assert doc.tags['param3'] == 10  # not overriden
    assert doc.tags['name'] == 'name'  # not override
    assert doc.tags['workspace'] == 'different_workspace'


def test_override_config_params_parallel(docker_image):
    flow = Flow(return_results=True).add(
        uses='docker://override-config-test',
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
