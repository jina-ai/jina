import os
import time

import pytest

from jina import Document, Client, __default_host__
from jina.logging.logger import JinaLogger
from daemon.clients import JinaDClient

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')

HOST = __default_host__
JINAD_PORT = 8000
REST_PORT_DBMS = 9000
REST_PORT_QUERY = 9001

logger = JinaLogger('test-dump')
client = JinaDClient(host=HOST, port=JINAD_PORT)

img_name = 'jina/scale-executor'


@pytest.fixture(scope='module')
def docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir, 'scale-executor'), tag=img_name)
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


def _create_flow(shards, replicas):
    workspace_id = client.workspaces.create(paths=[cur_dir])
    flow_id = client.flows.create(
        workspace_id=workspace_id,
        filename='flow.yml',
        envs={'JINAD_WORKSPACE': f'/tmp/jinad/{workspace_id}'},
    )
    return flow_id, workspace_id


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
@pytest.mark.parametrize('shards', [1, 2])
@pytest.mark.parametrize('old_replicas', [2, 3, 5])
@pytest.mark.parametrize('new_replicas', [3, 4])
def test_scale_flow_remote(
    executor_images, docker_compose, shards, old_replicas, new_replicas
):
    docs = [Document() for _ in range(200)]

    flow_id, workspace_id = _create_flow(shards, old_replicas)

    ret1 = Client(host=HOST, port=REST_PORT_QUERY, protocol='http').search(
        inputs=docs, return_results=True, request_size=10
    )
    assert len(ret1) == 20
    replica_ids = set()
    for r in ret1:
        assert len(r.docs) == 10
        for replica_id in r.docs.get_attributes('tags__replica_id'):
            replica_ids.add(replica_id)

    assert replica_ids == set(range(old_replicas))

    client.flows.update(
        id=flow_id,
        kind='scale',
        pod_name='scale_executor',
    )

    ret2 = Client(host=HOST, port=REST_PORT_QUERY, protocol='http').search(
        inputs=docs, return_results=True, request_size=10
    )

    assert len(ret2) == 20
    replica_ids = set()
    for r in ret2:
        assert len(r.docs) == 10
        for replica_id in r.docs.get_attributes('tags__replica_id'):
            replica_ids.add(replica_id)

    assert replica_ids == set(range(new_replicas))

    assert client.flows.delete(flow_id)
    assert client.workspaces.delete(workspace_id)
