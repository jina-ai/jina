import collections
import os
import time
import threading

import numpy as np
import pytest

from jina import Document, Flow, Executor, requests

cur_dir = os.path.dirname(os.path.abspath(__file__))


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
    assert len(set(shards)) == NUM_SHARDS


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


@pytest.mark.repeat(5)
@pytest.mark.timeout(60)
@pytest.mark.parametrize('uses', ['docker://test_rolling_update_docker'])
def test_thread_run(docs, mocker, reraise, docker_image, uses):
    def update_rolling(flow, pod_name):
        with reraise:
            flow.rolling_update(pod_name)

    error_mock = mocker.Mock()
    total_responses = []
    with Flow().add(
        uses=uses,
        name='executor1',
        replicas=2,
        shards=2,
        timeout_ready=5000,
    ) as flow:
        x = threading.Thread(
            target=update_rolling,
            args=(
                flow,
                'executor1',
            ),
        )
        for i in range(50):
            responses = flow.search(
                docs, on_error=error_mock, request_size=10, return_results=True
            )
            total_responses.extend(responses)
            if i == 5:
                x.start()
        x.join()
    error_mock.assert_not_called()
    assert len(total_responses) == (len(docs) * 50 / 10)


@pytest.mark.repeat(5)
@pytest.mark.timeout(60)
def test_vector_indexer_thread(config, docs, mocker, reraise):
    def update_rolling(flow, pod_name):
        with reraise:
            flow.rolling_update(pod_name)

    error_mock = mocker.Mock()
    total_responses = []
    with Flow().add(
        name='executor1',
        uses=DummyMarkExecutor,
        replicas=2,
        shards=3,
        timeout_ready=5000,
    ) as flow:
        for i in range(5):
            flow.search(docs, on_error=error_mock)
        x = threading.Thread(
            target=update_rolling,
            args=(
                flow,
                'executor1',
            ),
        )
        for i in range(40):
            responses = flow.search(
                docs, on_error=error_mock, request_size=10, return_results=True
            )
            total_responses.extend(responses)
            if i == 5:
                x.start()
        x.join()
    error_mock.assert_not_called()
    assert len(total_responses) == (len(docs) * 40 / 10)


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


@pytest.mark.parametrize(
    'replicas_and_shards',
    (
        ((3, 1),),
        ((2, 3),),
        ((2, 3), (3, 4), (2, 2), (2, 1)),
    ),
)
def test_port_configuration(replicas_and_shards):
    def validate_ports_replica(shard, replica_port_in, replica_port_out, shards):
        assert replica_port_in == shard.args.port_in
        assert shard.args.port_out == replica_port_out
        peas_args = shard.peas_args
        peas = peas_args['peas']
        assert len(peas) == shards
        if shards == 1:
            assert peas_args['head'] is None
            assert peas_args['tail'] is None
            assert peas[0].port_in == replica_port_in
            assert peas[0].port_out == replica_port_out
        else:
            shard_head = peas_args['head']
            shard_tail = peas_args['tail']
            assert shard.args.port_in == shard_head.port_in
            assert shard.args.port_out == shard_tail.port_out
            for pea in peas:
                assert shard_head.port_out == pea.port_in
                assert pea.port_out == shard_tail.port_in

    flow = Flow()
    for i, (replicas, shards) in enumerate(replicas_and_shards):
        flow.add(
            name=f'pod{i}',
            replicas=replicas,
            shards=shards,
            copy_flow=False,
        )

    with flow:
        pods = flow._pod_nodes

        for pod_name, pod in pods.items():
            if pod_name == 'gateway':
                continue
            if pod.args.replicas == 1:
                if int(pod.args.shards) == 1:
                    assert len(pod.peas_args['peas']) == 1
                else:
                    assert len(pod.peas_args) == 3
                shard_port_in = pod.args.port_in
                shard_port_out = pod.args.port_out
            else:
                shard_port_in = pod.head_args.port_out
                shard_port_out = pod.tail_args.port_in

            assert pod.head_args.port_in == pod.args.port_in
            assert pod.head_args.port_out == shard_port_in
            assert pod.tail_args.port_in == shard_port_out
            assert pod.tail_args.port_out == pod.args.port_out
            if pod.args.shards > 1:
                for shard in pod.shards:
                    validate_ports_replica(
                        shard,
                        shard_port_in,
                        shard_port_out,
                        getattr(pod.args, 'replicas', 1),
                    )
        assert pod


def test_num_peas(config):
    with Flow().add(
        name='executor1',
        uses='!DummyMarkExecutor',
        replicas=3,
        shards=4,
    ) as flow:
        assert flow.num_peas == (
            4 * (3 + 1 + 1)  # shards 4  # replicas 3  # pod head  # pod tail
            + 1  # compound pod head
            + 1  # compound pod tail1
            + 1  # gateway
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
    flow = Flow().add(
        name='executor1',
        uses=UpdateExecutor,
        replicas=2,
        parallel=3,
    )
    with flow:
        # test rolling update does not hang
        ret1 = flow.search(docs, return_results=True)
        flow.rolling_update(
            'executor1',
            dump_path='/tmp/dump_path2/',
            uses_with={'argument1': 'version2', 'argument2': 'version2'},
        )
        ret2 = flow.search(docs, return_results=True)

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
    flow = Flow().add(
        name='executor1',
        uses=DummyMarkExecutor,
        replicas=replicas,
    )
    with flow:
        ret1 = flow.search(docs, return_results=True, request_size=1)
        flow.rolling_update('executor1', None)
        flow.scale('executor1', replicas=scale_to)
        ret2 = flow.search(docs, return_results=True, request_size=1)

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
