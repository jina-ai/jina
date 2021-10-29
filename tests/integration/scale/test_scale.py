import pytest
import time
import os

from jina import Flow, Executor, Document, DocumentArray, requests

cur_dir = os.path.dirname(os.path.abspath(__file__))


class ScalableExecutor(Executor):
    def __init__(self, allow_failure=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.replica_id = self.runtime_args.replica_id
        self.shard_id = self.runtime_args.shard_id
        if self.replica_id > 3 and allow_failure:
            raise Exception(f' I fail when scaling above 4')

    @requests
    def foo(self, docs, *args, **kwargs):
        for doc in docs:
            doc.tags['replica_id'] = self.replica_id
            doc.tags['shard_id'] = self.shard_id


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


@pytest.mark.parametrize('shards', [1, 2])
@pytest.mark.parametrize('old_replicas', [2, 5])
@pytest.mark.parametrize('new_replicas', [3, 4])
def test_scale_successfully_zedruntime(shards, old_replicas, new_replicas):
    f = Flow().add(
        name='executor',
        uses=ScalableExecutor,
        uses_with={
            'allow_failure': new_replicas > old_replicas
        },  # I want to also test proper downscaling
        replicas=old_replicas,
        shards=shards,
        polling='ANY',
    )
    with f:
        ret1 = f.index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )
        f.scale(pod_name='executor', replicas=new_replicas)
        ret2 = f.index(
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

    assert replica_ids == set(range(old_replicas))

    assert len(ret2) == 20
    replica_ids = set()
    for r in ret2:
        assert len(r.docs) == 10
        for replica_id in r.docs.get_attributes('tags__replica_id'):
            replica_ids.add(replica_id)

    assert replica_ids == set(range(new_replicas))


@pytest.mark.parametrize('shards', [1, 2])
@pytest.mark.parametrize('old_replicas', [2, 3, 5])
@pytest.mark.parametrize('new_replicas', [3, 4])
def test_scale_successfully_containerruntime(
    docker_image_built, shards, old_replicas, new_replicas
):
    f = Flow().add(
        name='executor',
        uses=f'docker://{img_name}',
        replicas=old_replicas,
        uses_with={
            'allow_failure': new_replicas > old_replicas
        },  # I want to also test proper downscaling
        shards=shards,
        polling='ANY',
    )
    with f:
        ret1 = f.index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )
        f.scale(pod_name='executor', replicas=new_replicas)
        ret2 = f.index(
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

    assert replica_ids == set(range(old_replicas))

    assert len(ret2) == 20
    replica_ids = set()
    for r in ret2:
        assert len(r.docs) == 10
        for replica_id in r.docs.get_attributes('tags__replica_id'):
            replica_ids.add(replica_id)

    assert replica_ids == set(range(new_replicas))


@pytest.mark.parametrize('shards', [1, 2])
def test_scale_failure_zedruntime(shards):
    f = Flow().add(
        name='executor', uses=ScalableExecutor, replicas=2, shards=shards, polling='ANY'
    )
    with f:
        ret1 = f.index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )
        with pytest.raises(Exception):
            f.scale(pod_name='executor', replicas=5)
        ret2 = f.index(
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

    assert replica_ids == {0, 1}

    assert len(ret2) == 20
    replica_ids = set()
    for r in ret2:
        assert len(r.docs) == 10
        for replica_id in r.docs.get_attributes('tags__replica_id'):
            replica_ids.add(replica_id)

    assert replica_ids == {0, 1}


@pytest.mark.parametrize('shards', [1, 2])
def test_scale_failure_containerruntime(docker_image_built, shards):
    f = Flow().add(
        name='executor',
        uses=f'docker://{img_name}',
        replicas=2,
        shards=shards,
        polling='ANY',
    )
    with f:
        ret1 = f.index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )
        with pytest.raises(Exception):
            f.scale(pod_name='executor', replicas=5)
        ret2 = f.index(
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

    assert replica_ids == {0, 1}

    assert len(ret2) == 20
    replica_ids = set()
    for r in ret2:
        assert len(r.docs) == 10
        for replica_id in r.docs.get_attributes('tags__replica_id'):
            replica_ids.add(replica_id)

    assert replica_ids == {0, 1}
