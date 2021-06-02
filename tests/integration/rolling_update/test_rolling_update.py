import collections
import os
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
            doc.tags['shard'] = self.runtime_args.pea_id
            doc.tags['reference'] = id(self)

    def close(self) -> None:
        import os

        os.makedirs(self.workspace, exist_ok=True)


def test_normal(docs):
    NUM_REPLICAS = 3
    NUM_SHARDS = 2
    doc_id_path = collections.OrderedDict()

    def handle_search_result(resp):
        for doc in resp.data.docs:
            doc_id_path[int(doc.id)] = (doc.tags['replica'], doc.tags['shard'])

    flow = Flow().add(
        name='pod1',
        uses=DummyMarkExecutor,
        replicas=NUM_REPLICAS,
        parallel=NUM_SHARDS,
    )
    with flow:
        flow.search(inputs=docs, request_size=1, on_done=handle_search_result)

    assert len(doc_id_path.keys()) == len(docs)

    num_used_replicas = len(set(map(lambda x: x[0], doc_id_path.values())))
    assert num_used_replicas == NUM_REPLICAS

    shards = collections.defaultdict(list)
    for replica, shard in doc_id_path.values():
        shards[replica].append(shard)

    assert len(shards.keys()) == NUM_REPLICAS

    for shard_list in shards.values():
        assert len(set(shard_list)) == NUM_SHARDS


@pytest.mark.timeout(30)
def test_simple_run(docs):
    flow = Flow().add(
        name='pod1',
        replicas=2,
        parallel=3,
    )
    with flow:
        # test rolling update does not hang
        flow.search(docs)
        flow.rolling_update('pod1', None)
        flow.search(docs)


@pytest.mark.repeat(5)
@pytest.mark.timeout(30)
def test_thread_run(docs, mocker, reraise):
    def update_rolling(flow, pod_name):
        with reraise:
            flow.rolling_update(pod_name)

    error_mock = mocker.Mock()
    with Flow().add(
        name='pod1',
        replicas=2,
        parallel=2,
        timeout_ready=5000,
    ) as flow:
        x = threading.Thread(
            target=update_rolling,
            args=(
                flow,
                'pod1',
            ),
        )
        for i in range(50):
            flow.search(docs, on_error=error_mock)
            if i == 5:
                x.start()
        x.join()
    error_mock.assert_not_called()


@pytest.mark.repeat(5)
@pytest.mark.timeout(30)
def test_vector_indexer_thread(config, docs, mocker, reraise):
    def update_rolling(flow, pod_name):
        with reraise:
            flow.rolling_update(pod_name)

    error_mock = mocker.Mock()
    with Flow().add(
        name='pod1',
        uses=DummyMarkExecutor,
        replicas=2,
        parallel=3,
        timeout_ready=5000,
    ) as flow:
        for i in range(5):
            flow.search(docs, on_error=error_mock)
        x = threading.Thread(
            target=update_rolling,
            args=(
                flow,
                'pod1',
            ),
        )
        for i in range(40):
            flow.search(docs, on_error=error_mock)
            if i == 5:
                x.start()
        x.join()
    error_mock.assert_not_called()


def test_workspace(config, tmpdir, docs):
    with Flow().add(
        name='pod1',
        uses=DummyMarkExecutor,
        workspace=str(tmpdir),
        replicas=2,
        parallel=3,
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
    'replicas_and_parallel',
    (
        ((3, 1),),
        ((2, 3),),
        ((2, 3), (3, 4), (2, 2), (2, 1)),
    ),
)
def test_port_configuration(replicas_and_parallel):
    def extract_pod_args(pod):
        if 'replicas' not in pod.args or int(pod.args.replicas) == 1:
            head_args = pod.peas_args['head']
            tail_args = pod.peas_args['tail']
            middle_args = pod.peas_args['peas']
        else:
            head_args = pod.head_args
            tail_args = pod.tail_args
            middle_args = pod.replicas_args
        return pod, head_args, tail_args, middle_args

    def get_outer_ports(pod, head_args, tail_args, middle_args):

        if not 'replicas' in pod.args or int(pod.args.replicas) == 1:
            if not 'parallel' in pod.args or int(pod.args.parallel) == 1:
                assert tail_args is None
                assert head_args is None
                replica = middle_args[0]  # there is only one
                return replica.port_in, replica.port_out
            else:
                return pod.head_args.port_in, pod.tail_args.port_out
        else:
            assert pod.args.replicas == len(middle_args)
            return pod.head_args.port_in, pod.tail_args.port_out

    def validate_ports_pods(pods):
        for i in range(len(pods) - 1):
            _, port_out = get_outer_ports(*extract_pod_args(pods[i]))
            port_in_next, _ = get_outer_ports(*extract_pod_args(pods[i + 1]))
            assert port_out == port_in_next

    def validate_ports_replica(replica, replica_port_in, replica_port_out, parallel):
        assert replica_port_in == replica.args.port_in
        assert replica.args.port_out == replica_port_out
        peas_args = replica.peas_args
        peas = peas_args['peas']
        assert len(peas) == parallel
        if parallel == 1:
            assert peas_args['head'] is None
            assert peas_args['tail'] is None
            assert peas[0].port_in == replica_port_in
            assert peas[0].port_out == replica_port_out
        else:
            shard_head = peas_args['head']
            shard_tail = peas_args['tail']
            assert replica.args.port_in == shard_head.port_in
            assert replica.args.port_out == shard_tail.port_out
            for pea in peas:
                assert shard_head.port_out == pea.port_in
                assert pea.port_out == shard_tail.port_in

    flow = Flow()
    for i, (replicas, parallel) in enumerate(replicas_and_parallel):
        flow.add(
            name=f'pod{i}',
            replicas=replicas,
            parallel=parallel,
            port_in=f'51{i}00',
            # info: needs to be set in this test since the test is asserting pod args with pod tail args
            port_out=f'51{i + 1}00',  # outside this test, it don't have to be set
            copy_flow=False,
        )

    with flow:
        pods = flow._pod_nodes
        validate_ports_pods(
            [pods['gateway']]
            + [pods[f'pod{i}'] for i in range(len(replicas_and_parallel))]
            + [pods['gateway']]
        )
        for pod_name, pod in pods.items():
            if pod_name == 'gateway':
                continue
            if pod.args.replicas == 1:
                if int(pod.args.parallel) == 1:
                    assert len(pod.peas_args['peas']) == 1
                else:
                    assert len(pod.peas_args) == 3
                replica_port_in = pod.args.port_in
                replica_port_out = pod.args.port_out
            else:
                replica_port_in = pod.head_args.port_out
                replica_port_out = pod.tail_args.port_in

            assert pod.head_pea.args.port_in == pod.args.port_in
            assert pod.head_pea.args.port_out == replica_port_in
            assert pod.tail_pea.args.port_in == replica_port_out
            assert pod.tail_pea.args.port_out == pod.args.port_out
            if pod.args.replicas > 1:
                for replica in pod.replicas:
                    validate_ports_replica(
                        replica,
                        replica_port_in,
                        replica_port_out,
                        getattr(pod.args, 'parallel', 1),
                    )
        assert pod


def test_num_peas(config):
    with Flow().add(
        name='pod1',
        uses='!DummyMarkExecutor',
        replicas=3,
        parallel=4,
    ) as flow:
        assert flow.num_peas == (
            3 * (4 + 1 + 1)  # replicas 3  # parallel 4  # pod head  # pod tail
            + 1  # compound pod head
            + 1  # compound pod tail
            + 1  # gateway
        )


@pytest.mark.repeat(5)
@pytest.mark.timeout(30)
def test_distinct_executor_ids(config, docs, mocker, reraise):
    def update_rolling(flow, pod_name):
        with reraise:
            flow.rolling_update(pod_name)

    ids = set()

    error_mock = mocker.Mock()
    with Flow(return_results=True).add(
        name='pod1',
        uses=DummyMarkExecutor,
        replicas=2,
        parallel=1,
        timeout_ready=5000,
    ) as flow:
        for i in range(5):
            flow.search(docs, on_error=error_mock)
        x = threading.Thread(
            target=update_rolling,
            args=(
                flow,
                'pod1',
            ),
        )
        for i in range(40):
            result = flow.search(docs)
            id = result[0].docs[0].tags['reference']
            ids.add(id)
            if i == 5:
                x.start()
        x.join()
    error_mock.assert_not_called()
    assert len(ids) >= 3  # seems we cannot guarantee that they will all be reached
