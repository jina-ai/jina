import os
import time
import multiprocessing
from functools import partial

import pytest

from jina import Flow, Document, DocumentArray, Client

cur_dir = os.path.dirname(os.path.abspath(__file__))
IMG_NAME = 'jina/scale-executor'

NUM_CONCURRENT_CLIENTS = 20
NUM_DOCS_SENT_BY_CLIENTS = 50
CLOUD_HOST = 'localhost:8000'
exposed_port = 12345


@pytest.fixture
def pod_params(request):
    num_replicas, scale_to, shards = request.param
    return num_replicas, scale_to, shards


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


@pytest.fixture
def remote_flow_with_container_runtime(pod_params, docker_image_built):
    num_replicas, scale_to, shards = pod_params
    return Flow(port_expose=exposed_port).add(
        name='executor',
        uses=f'docker://{IMG_NAME}',
        replicas=num_replicas,
        shards=shards,
        polling='ANY',
        host=CLOUD_HOST,
    )


@pytest.fixture(params=['remote_flow_with_container_runtime'])
def remote_flow_with_runtime(request):
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize(
    'pod_params',  # (num_replicas, scale_to, shards)
    [
        (2, 3, 1),  # scale up 1 replica with 1 shard
        (2, 3, 2),  # scale up 1 replica with 2 shards
        (3, 1, 1),  # scale down 2 replicas with 1 shard
        (3, 1, 2),  # scale down 2 replicas with 2 shards
    ],
    indirect=True,
)
def test_scale_success(remote_flow_with_runtime: Flow, pod_params):
    num_replicas, scale_to, shards = pod_params
    with remote_flow_with_runtime as f:
        ret1 = Client(port=exposed_port).index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )
        f.scale(pod_name='executor', replicas=scale_to)
        ret2 = Client(port=exposed_port).index(
            inputs=DocumentArray([Document() for _ in range(200)]),
            return_results=True,
            request_size=10,
        )

        assert len(ret1) == 20
        replicas = set()
        for r in ret1:
            assert len(r.docs) == 10
            # replicas are identified via their docker id
            for id in r.docs[:, 'tags__uid']:
                replicas.add(id)

        assert len(replicas) == num_replicas * shards

        assert len(ret2) == 20
        replicas = set()
        for r in ret2:
            assert len(r.docs) == 10
            for id in r.docs[:, 'tags__uid']:
                replicas.add(id)

        assert len(replicas) == scale_to * shards


@pytest.mark.parametrize(
    'pod_params',
    [
        (2, 3, 1),
        (3, 2, 1),
    ],
    indirect=True,
)
@pytest.mark.parametrize('protocol', ['grpc', 'websocket', 'http'])
def test_scale_with_concurrent_client(
    remote_flow_with_runtime: Flow, pod_params, protocol
):
    def peer_client(port, protocol, peer_hash, queue):
        rv = Client(protocol=protocol, port=port).index(
            [Document(text=peer_hash) for _ in range(NUM_DOCS_SENT_BY_CLIENTS)],
            request_size=5,
            return_results=True,
        )
        for r in rv:
            for doc in r.docs:
                # our proto objects are not fit to be sent by queues
                queue.put(doc.text)

    num_replicas, scale_to, _ = pod_params
    queue = multiprocessing.Queue()
    remote_flow_with_runtime.protocol = protocol
    with remote_flow_with_runtime as f:

        port_expose = f.port_expose

        thread_pool = []
        for peer_id in range(NUM_CONCURRENT_CLIENTS):
            # test
            t = multiprocessing.Process(
                target=partial(peer_client, port_expose, protocol, str(peer_id), queue)
            )
            t.start()
            thread_pool.append(t)

        f.scale(pod_name='executor', replicas=scale_to)

        for t in thread_pool:
            t.join()

        c = Client(protocol=protocol, port=port_expose)
        rv = c.index(
            [Document() for _ in range(5)], request_size=1, return_results=True
        )

    all_docs = []
    while not queue.empty():
        all_docs.append(queue.get())

    assert len(all_docs) == NUM_CONCURRENT_CLIENTS * NUM_DOCS_SENT_BY_CLIENTS

    assert len(rv) == 5

    for r in rv:
        assert len(r.docs) == 1
