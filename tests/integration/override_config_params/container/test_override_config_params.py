import os
import time
import pytest

from jina import Flow, Document, Client

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture()
def docker_image():
    import docker

    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir), tag='override-config-test')
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()
    client.close()


@pytest.fixture()
def flow(request, port_generator):
    exposed_port = port_generator()
    flow_src = request.param
    if flow_src == 'yml':
        return Flow(port=exposed_port).load_config(os.path.join(cur_dir, 'flow.yml'))
    elif flow_src == 'python':
        return Flow(port=exposed_port).add(
            uses='docker://override-config-test',
            uses_with={'param1': 50, 'param2': 30},
            uses_metas={'workspace': 'different_workspace'},
        )


@pytest.mark.parametrize('flow', ['yml', 'python'], indirect=['flow'])
def test_override_config_params(docker_image, flow):
    with flow:
        resps = Client(port=flow.port).search(
            inputs=[Document()], return_responses=True
        )
    doc = resps[0].docs[0]
    assert doc.tags['param1'] == 50
    assert doc.tags['param2'] == 30
    assert doc.tags['param3'] == 10  # not overriden
    assert doc.tags['name'] == 'name'  # not override
    assert doc.tags['workspace'] == 'different_workspace'


def test_override_config_params_shards(docker_image, port_generator):
    exposed_port = port_generator()
    flow = Flow(port=exposed_port).add(
        uses='docker://override-config-test',
        uses_with={'param1': 50, 'param2': 30},
        uses_metas={'workspace': 'different_workspace'},
        shards=2,
    )
    with flow:
        resps = Client(port=exposed_port).search(
            inputs=[Document()], return_responses=True
        )
    doc = resps[0].docs[0]
    assert doc.tags['param1'] == 50
    assert doc.tags['param2'] == 30
    assert doc.tags['param3'] == 10  # not overriden
    assert doc.tags['name'] == 'name'  # not override
    assert doc.tags['workspace'] == 'different_workspace'
