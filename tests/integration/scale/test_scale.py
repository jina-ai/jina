import os
import time
import multiprocessing
from functools import partial

import pytest

from jina import Flow, Executor, Document, DocumentArray, requests
from jina.excepts import RuntimeFailToStart, ScalingFails
from jina.clients import Client

cur_dir = os.path.dirname(os.path.abspath(__file__))
IMG_NAME = 'jina/scale-executor'


class ScalableExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.replica_id = self.runtime_args.replica_id
        self.shard_id = self.runtime_args.shard_id

    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.tags['replica_id'] = self.replica_id
            doc.tags['shard_id'] = self.shard_id


@pytest.fixture(scope='module')
def docker_image_built():
    import docker

    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir, 'scale-executor'), tag=IMG_NAME)
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


@pytest.fixture
def pod_params(request):
    num_replicas, scale_to, shards = request.param
    return num_replicas, scale_to, shards


@pytest.fixture
def flow_with_zed_runtime(pod_params):
    num_replicas, scale_to, shards = pod_params
    return Flow().add(
        name='executor',
        uses=ScalableExecutor,
        replicas=num_replicas,
        shards=shards,
        polling='ANY',
    )


@pytest.fixture
def flow_with_container_runtime(pod_params, docker_image_built):
    num_replicas, scale_to, shards = pod_params
    return Flow().add(
        name='executor',
        uses=f'docker://{IMG_NAME}',
        replicas=num_replicas,
        shards=shards,
        polling='ANY',
    )


@pytest.fixture(params=['flow_with_zed_runtime', 'flow_with_container_runtime'])
def flow_with_runtime(request):
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize(
    'pod_params',  # (num_replicas, scale_to, shards)
    [
        (2, 3, 1),  # scale up 1 replica with 1 shard
        (2, 3, 2),  # scale up 1 replica with 2 shards
        (3, 1, 1),  # scale down 2 replicas with 1 shard
        (3, 1, 2),  # scale down 2 replicas with 1 shard
    ],
    indirect=True,
)
def test_scale_success(flow_with_runtime, pod_params):
    num_replicas, scale_to, shards = pod_params
    with flow_with_runtime as f:
        ret1 = f.index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )
        f.scale(pod_name='executor', replicas=scale_to)
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

        assert replica_ids == set(range(num_replicas))

        assert len(ret2) == 20
        replica_ids = set()
        for r in ret2:
            assert len(r.docs) == 10
            for replica_id in r.docs.get_attributes('tags__replica_id'):
                replica_ids.add(replica_id)

        assert replica_ids == set(range(scale_to))


@pytest.mark.parametrize(
    'pod_params',
    [
        (2, 5, 1),
        (2, 5, 2),
    ],
    indirect=True,
)
def test_scale_fail(flow_with_runtime, pod_params, mocker):
    # note, this test only consist of scale up fail.
    # the only way to make scale down fail is to raise Exception while pod close
    # while it also breaks the test itself.
    num_replicas, scale_to, shards = pod_params
    mocker.patch(
        'jina.peapods.peas.BasePea.async_wait_start_success',
        side_effect=RuntimeFailToStart,
    )
    with flow_with_runtime as f:
        ret1 = f.index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )
        with pytest.raises(ScalingFails):
            f.scale(pod_name='executor', replicas=scale_to)

        ret2 = f.index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )

    assert len(ret1) == 20
    assert len(ret2) == 20

    replica1_ids = set()
    replica2_ids = set()
    for r1, r2 in zip(ret1, ret2):
        assert len(r1.docs) == 10
        assert len(r2.docs) == 10
        for replica_id in r1.docs.get_attributes('tags__replica_id'):
            replica1_ids.add(replica_id)
        for replica_id in r2.docs.get_attributes('tags__replica_id'):
            replica2_ids.add(replica_id)
    assert replica1_ids == replica2_ids == {0, 1}


@pytest.mark.parametrize(
    'pod_params',
    [
        (2, 3, 1),
    ],
    indirect=True,
)
@pytest.mark.parametrize('protocol', ['grpc', 'websocket', 'http'])
def test_scale_with_concurrent_client(flow_with_runtime, pod_params, protocol):
    def peer_client(port, protocol, peer_hash, queue):
        c = Client(protocol=protocol, port=port)
        ret = queue.get()
        rv = c.index(Document(text=peer_hash), return_results=True)
        for r in rv:
            for replica_id in r.docs.get_attributes('tags__replica_id'):
                ret.append(replica_id)
        queue.put(ret)

    num_replicas, scale_to, _ = pod_params
    ret = []
    queue = multiprocessing.Queue()
    queue.put(ret)

    with flow_with_runtime as f:
        f.protocol = protocol
        port_expose = f.port_expose

        thread_pool = []
        for peer_id in range(5):
            t = multiprocessing.Process(
                target=partial(peer_client, port_expose, protocol, str(peer_id), queue),
                daemon=True,
            )
            t.start()
            f.scale(pod_name='executor', replicas=scale_to)
            thread_pool.append(t)

        for t in thread_pool:
            t.join()

    replicas = queue.get()
    assert len(set(replicas)) == scale_to
