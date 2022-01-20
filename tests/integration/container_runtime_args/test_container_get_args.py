import time
import os

import pytest

from jina import Flow, Document, DocumentArray, Client

cur_dir = os.path.dirname(os.path.abspath(__file__))

img_name = 'jina/replica-exec'
exposed_port = 12345


@pytest.fixture(scope='function')
def docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir, 'replica-exec'), tag=img_name)
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


@pytest.mark.parametrize('shards', [1, 2])
@pytest.mark.parametrize('replicas', [1, 3, 4])
def test_containerruntime_args(docker_image_built, shards, replicas):
    f = Flow(port_expose=exposed_port).add(
        name='executor_container',
        uses=f'docker://{img_name}',
        replicas=replicas,
        shards=shards,
        polling='ANY',
    )
    with f:
        ret1 = Client(port=exposed_port).index(
            inputs=DocumentArray([Document() for _ in range(2000)]),
            return_results=True,
            request_size=10,
        )

    assert len(ret1) == 200
    unique_replicas = set()
    shard_ids = set()
    for r in ret1:
        assert len(r.docs) == 10
        for replica in r.docs[:, 'tags__replica']:
            unique_replicas.add(replica)
        for shard_id in r.docs[:, 'tags__shard_id']:
            shard_ids.add(shard_id)
        for doc in r.docs:
            assert doc.tags['shards'] == shards

    assert shard_ids == set(range(shards))
    assert len(unique_replicas) == replicas * shards
