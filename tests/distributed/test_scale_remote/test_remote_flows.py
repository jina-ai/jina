import os
import time
import pytest

from daemon.clients import JinaDClient
from jina import Client, Document, DocumentArray, __default_host__

cur_dir = os.path.dirname(os.path.abspath(__file__))
jinad_client = JinaDClient(host=__default_host__, port=8000)
IMG_NAME = 'jina/scale-executor'


@pytest.fixture(scope='function')
def docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(
        path=os.path.join(cur_dir, '../../integration/scale/scale-executor'),
        tag=IMG_NAME,
    )
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


@pytest.mark.parametrize('filename', ['flow_zed.yml', 'flow_container.yml'])
@pytest.mark.parametrize(
    'pod_params',  # (num_replicas, scale_to, shards)
    [
        (2, 3, 1),  # scale up 1 replica with 1 shard
        (3, 1, 1),  # scale down 2 replicas with 1 shard
        pytest.param(
            (2, 3, 2),  # scale up 2 replicas with 2 shards
            marks=pytest.mark.skip(
                reason='https://github.com/jina-ai/jina/issues/3941'
            ),
        ),
        pytest.param(
            (3, 1, 2),  # scale down 2 replicas with 2 shards
            marks=pytest.mark.skip(
                reason='https://github.com/jina-ai/jina/issues/3941'
            ),
        ),
    ],
)
def test_scale_remote_flow(docker_image_built, filename, pod_params):
    num_replicas, scale_to, shards = pod_params
    flow_id = None
    try:
        workspace_id = jinad_client.workspaces.create(
            paths=[
                cur_dir,
                os.path.join(cur_dir, '../test_scale_remote_executors/executors.py'),
            ]
        )
        flow_id = jinad_client.flows.create(
            workspace_id=workspace_id,
            filename=filename,
            envs={'REPLICAS': num_replicas, 'SHARDS': shards},
        )

        ret1 = Client(port=12345).index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )
        jinad_client.flows.scale(id=flow_id, pod_name='executor', replicas=scale_to)
        ret2 = Client(port=12345).index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )

        assert len(ret1) == 20
        replica_ids = set()
        for r in ret1:
            assert len(r.docs) == 10
            for replica_id in r.docs.get_attributes('tags__replica_id'):
                replica_ids.add(replica_id)

        assert replica_ids == set(range(num_replicas))

        assert len(ret2) == 20
        replica_ids = set()
        for r in ret2:
            assert len(r.docs) == 10
            for replica_id in r.docs.get_attributes('tags__replica_id'):
                replica_ids.add(replica_id)

        assert replica_ids == set(range(scale_to))
    finally:
        if flow_id:
            assert jinad_client.flows.delete(flow_id), 'Flow termination failed'
            print(f'Remote Flow {flow_id} successfully terminated')
