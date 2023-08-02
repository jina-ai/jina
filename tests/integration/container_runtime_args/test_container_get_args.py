import pytest

from jina import Client, Document, DocumentArray, Flow


@pytest.mark.parametrize('shards', [1, 2])
@pytest.mark.parametrize('replicas', [1, 3, 4])
def test_containerruntime_args(
    docker_image_name, docker_image_built, shards, replicas, port_generator
):
    exposed_port = port_generator()
    f = Flow(port=exposed_port).add(
        name='executor_container',
        uses=f'docker://{docker_image_name}',
        replicas=replicas,
        shards=shards,
        polling='ANY',
    )
    with f:
        ret1 = Client(port=exposed_port).index(
            inputs=DocumentArray([Document() for _ in range(2000)]),
            request_size=10,
            return_responses=True,
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
