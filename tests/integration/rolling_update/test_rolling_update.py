import collections
import multiprocessing
import os
import threading
import time

import numpy as np
import pytest

from jina import Document, Flow, Executor, requests, Client

cur_dir = os.path.dirname(os.path.abspath(__file__))
exposed_port = 12345


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_REPLICA_DIR'] = str(tmpdir)
    yield
    del os.environ['JINA_REPLICA_DIR']


@pytest.fixture
def docs():
    return [
        Document(id=str(i), text=f'doc {i}', embedding=np.array([i] * 5))
        for i in range(20)
    ]


class DummyMarkExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metas.name = 'dummy'

    @requests
    def foo(self, docs, *args, **kwargs):
        for doc in docs:
            doc.tags['replica'] = self.runtime_args.replica_id
            doc.tags['shard'] = self.runtime_args.shard_id

    def close(self) -> None:
        import os

        os.makedirs(self.workspace, exist_ok=True)


def test_normal(docs):
    NUM_REPLICAS = 3
    NUM_SHARDS = 2
    doc_id_path = collections.OrderedDict()

    def handle_search_result(resp):
        for doc in resp.data.docs:
            if int(doc.id) not in doc_id_path:
                doc_id_path[int(doc.id)] = []
            doc_id_path[int(doc.id)].append((doc.tags['replica'], doc.tags['shard']))

    flow = Flow().add(
        name='executor1',
        uses=DummyMarkExecutor,
        replicas=NUM_REPLICAS,
        shards=NUM_SHARDS,
    )
    with flow:
        flow.search(inputs=docs, request_size=1, on_done=handle_search_result)

    assert len(doc_id_path.keys()) == len(docs)

    replica_shards = [
        tag_item for tag_items in doc_id_path.values() for tag_item in tag_items
    ]
    replicas = [r for r, s in replica_shards]
    shards = [s for r, s in replica_shards]

    assert len(set(replicas)) == NUM_REPLICAS
    # shard results are reduced
    assert len(set(shards)) == 1


@pytest.mark.timeout(60)
def test_simple_run(docs):
    flow = Flow().add(
        name='executor1',
        replicas=2,
        shards=3,
    )
    with flow:
        # test rolling update does not hang
        flow.search(docs)
        flow.rolling_update('executor1', None)
        flow.search(docs)


@pytest.fixture()
def docker_image():
    import docker

    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir), tag='test_rolling_update_docker')
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()
    client.close()


# TODO: this should be repeatable, but its not due to head/gateway not being containerized
# @pytest.mark.repeat(5)
@pytest.mark.timeout(60)
@pytest.mark.parametrize('uses', ['docker://test_rolling_update_docker'])
def test_search_while_updating(docs, reraise, docker_image, uses):
    request_count = 50
    shards = 2

    def update_rolling(flow, pod_name, start_event):
        start_event.wait()
        with reraise:
            flow.rolling_update(pod_name)

    with Flow().add(
        uses=uses,
        name='executor1',
        replicas=2,
        shards=shards,
        timeout_ready=5000,
    ) as flow:
        start_event = multiprocessing.Event()
        result_queue = multiprocessing.Queue()

        client_process = multiprocessing.Process(
            target=send_requests,
            args=(
                flow.port_expose,
                start_event,
                result_queue,
                len(docs),
                request_count,
            ),
        )
        client_process.start()
        update_rolling(flow, 'executor1', start_event)
        client_process.join()

    total_docs = 0
    while result_queue.qsize():
        total_docs += len(result_queue.get())
    assert total_docs == len(docs) * request_count


# TODO: this should be repeatable, but its not due to head/gateway not being containerized
# @pytest.mark.repeat(5)
@pytest.mark.timeout(60)
def test_vector_indexer_thread(config, docs, reraise):
    def update_rolling(flow, pod_name, start_event):
        start_event.wait()
        with reraise:
            flow.rolling_update(pod_name)

    with Flow().add(
        name='executor1',
        uses=DummyMarkExecutor,
        replicas=2,
        shards=3,
        timeout_ready=5000,
    ) as flow:
        start_event = multiprocessing.Event()

        client_process = multiprocessing.Process(
            target=send_requests,
            args=(flow.port_expose, start_event, multiprocessing.Queue(), len(docs), 5),
        )
        client_process.start()
        client_process.join()
        result_queue = multiprocessing.Queue()
        client_process = multiprocessing.Process(
            target=send_requests,
            args=(flow.port_expose, start_event, result_queue, len(docs), 40),
        )
        client_process.start()
        update_rolling(flow, 'executor1', start_event)
        client_process.join()

    total_docs = 0
    while result_queue.qsize():
        total_docs += len(result_queue.get())
    assert total_docs == len(docs) * 40


def test_workspace(config, tmpdir, docs):
    with Flow().add(
        name='executor1',
        uses=DummyMarkExecutor,
        workspace=str(tmpdir),
        replicas=2,
        shards=3,
    ) as flow:
        # in practice, we don't send index requests to the compound pod this is just done to test the workspaces
        for i in range(10):
            flow.index(docs)

    # validate created workspaces
    assert set(os.listdir(str(tmpdir))) == {'dummy'}
    assert set(os.listdir(os.path.join(tmpdir, 'dummy'))) == {'0', '1'}
    for replica_id in {'0', '1'}:
        assert set(os.listdir(os.path.join(tmpdir, 'dummy', replica_id))) == {
            '0',
            '1',
            '2',
        }


def test_num_peas(config):
    with Flow().add(
        name='executor1',
        uses='!DummyMarkExecutor',
        replicas=3,
        shards=4,
    ) as flow:
        assert flow.num_peas == (
            4 * 3 + 1 + 1  # shards 4  # replicas 3  # pod head  # gateway
        )


class UpdateExecutor(Executor):
    def __init__(
        self,
        dump_path: str = '/tmp/dump_path1/',
        argument1: str = 'version1',
        argument2: str = 'version1',
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._dump_path = dump_path
        self._argument1 = argument1
        self._argument2 = argument2

    @requests
    def run(self, docs, **kwargs):
        for doc in docs:
            doc.tags['dump_path'] = self._dump_path
            doc.tags['arg1'] = self._argument1
            doc.tags['arg2'] = self._argument2


@pytest.mark.timeout(60)
def test_override_uses_with(docs):
    flow = Flow(port_expose=exposed_port).add(
        name='executor1',
        uses=UpdateExecutor,
        replicas=2,
        parallel=3,
    )
    with flow:
        # test rolling update does not hang
        ret1 = Client(port=exposed_port).search(docs, return_results=True)
        flow.rolling_update(
            'executor1',
            uses_with={
                'dump_path': '/tmp/dump_path2/',
                'argument1': 'version2',
                'argument2': 'version2',
            },
        )
        ret2 = Client(port=exposed_port).search(docs, return_results=True)

    assert len(ret1) > 0
    assert len(ret1[0].docs) > 0
    for doc in ret1[0].docs:
        assert doc.tags['dump_path'] == '/tmp/dump_path1/'
        assert doc.tags['arg1'] == 'version1'
        assert doc.tags['arg2'] == 'version1'

    assert len(ret2) > 0
    assert len(ret2[0].docs) > 0
    for doc in ret2[0].docs:
        assert doc.tags['dump_path'] == '/tmp/dump_path2/'
        assert doc.tags['arg1'] == 'version2'
        assert doc.tags['arg2'] == 'version2'


@pytest.mark.timeout(60)
@pytest.mark.parametrize(
    'replicas, scale_to, expected_before_scale, expected_after_scale',
    [(2, 3, {0, 1}, {0, 1, 2}), (3, 2, {0, 1, 2}, {0, 1})],
)
def test_scale_after_rolling_update(
    docs, replicas, scale_to, expected_before_scale, expected_after_scale
):
    flow = Flow(port_expose=exposed_port).add(
        name='executor1',
        uses=DummyMarkExecutor,
        replicas=replicas,
    )
    with flow:
        ret1 = Client(port=exposed_port).search(
            docs, return_results=True, request_size=1
        )
        flow.rolling_update('executor1', None)
        flow.scale('executor1', replicas=scale_to)
        ret2 = Client(port=exposed_port).search(
            docs, return_results=True, request_size=1
        )

    replica_ids = set()
    for r in ret1:
        for replica_id in r.docs.get_attributes('tags__replica'):
            replica_ids.add(replica_id)

    assert replica_ids == expected_before_scale

    replica_ids = set()
    for r in ret2:
        for replica_id in r.docs.get_attributes('tags__replica'):
            replica_ids.add(replica_id)
    assert replica_ids == expected_after_scale


def send_requests(
    port_expose,
    start_rolling_update_event: multiprocessing.Event,
    result_queue: multiprocessing.Queue,
    doc_count: int,
    request_count: int,
):
    client = Client(port=port_expose)
    for i in range(request_count):
        responses = client.search(
            [Document(id=f'{idx}', text=f'doc{idx}') for idx in range(doc_count)],
            request_size=10,
            return_results=True,
        )
        for r in responses:
            result_queue.put(r.docs.texts)
        if i == 5:
            start_rolling_update_event.set()
            # give the rolling update some time to kick in
            time.sleep(0.1)
