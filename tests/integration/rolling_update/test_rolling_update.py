import os
import threading
import pytest
import numpy as np

from jina import Document
from jina.flow import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_REPLICA_DIR'] = str(tmpdir)
    yield
    del os.environ['JINA_REPLICA_DIR']


def test_normal():
    flow = Flow().add(
        name='pod1',
        replicas=2,
        parallel=3,
        port_in=5100,
        port_out=5200,
    )
    with flow:
        flow.index(Document(text='documents before rolling update'))


def test_simple_run():
    flow = Flow().add(
        name='pod1',
        replicas=2,
        parallel=3,
        port_in=5100,
        port_out=5200,
    )
    with flow:
        flow.index(Document(text='documents before rolling update'))
        flow.rolling_update('pod1')
        flow.index(Document(text='documents after rolling update'))


def test_thread_run():
    flow = Flow().add(
        name='pod1',
        replicas=2,
        parallel=2,
        port_in=5100,
        port_out=5200,
    )
    with flow:
        x = threading.Thread(target=flow.rolling_update, args=('pod1',))
        x.start()
        # TODO remove the join to make it asynchronous again
        x.join()
        # TODO there is a problem with the gateway even after request times out - open issue
        for i in range(600):
            flow.search(Document(text='documents after rolling update'))


def test_vector_indexer_thread(config):
    with Flow().add(
        name='pod1',
        uses=os.path.join(cur_dir, 'yaml/index_vector.yml'),
        replicas=2,
        parallel=3,
        port_in=5100,
        port_out=5200,
    ) as flow:
        for i in range(5):
            flow.search(Document(text=f'documents before rolling update {i}'))
        x = threading.Thread(target=flow.rolling_update, args=('pod1',))
        x.start()
        # TODO there is a problem with the gateway even after request times out - open issue
        # TODO remove the join to make it asynchronous again
        x.join()
        for i in range(40):
            flow.search(Document(text='documents after rolling update'))


def test_workspace(config, tmpdir):
    with Flow().add(
        name='pod1',
        uses=os.path.join(cur_dir, 'yaml/simple_index_vector.yml'),
        replicas=2,
        parallel=3,
        port_in=5100,
        port_out=5200,
    ) as flow:
        # in practice, we don't send index requests to the compound pod this is just done to test the workspaces
        for i in range(10):
            flow.index(Document(text=f'indexed doc {i}', embedding=np.array([i] * 5)))

        # validate created workspaces
        dirs = set(os.listdir(tmpdir))
        expected_dirs = {
            'vecidx-0-0',
            'vecidx-0-1',
            'vecidx-0-2',
            'vecidx-1-0',
            'vecidx-1-1',
            'vecidx-1-2',
        }
        assert dirs == expected_dirs


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
            head_args = pod.replicas_args['head']
            tail_args = pod.replicas_args['tail']
            middle_args = pod.replicas_args['replicas']
        return pod, head_args, tail_args, middle_args

    def get_outer_ports(pod, head_args, tail_args, middle_args):

        if not 'replicas' in pod.args or int(pod.args.replicas) == 1:
            if not 'parallel' in pod.args or int(pod.args.parallel) == 1:
                assert tail_args is None
                assert head_args is None
                replica = middle_args[0]  # there is only one
                return replica.port_in, replica.port_out
            else:
                return pod.peas_args['head'].port_in, pod.peas_args['tail'].port_out
        else:
            assert pod.args.replicas == len(middle_args)
            return pod.replicas_args['head'].port_in, pod.replicas_args['tail'].port_out

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
            port_in=f'51{i}00',  # info: needs to be set in this test since the test is asserting pod args with pod tail args
            port_out=f'51{i+1}00',  # outside this test, it don't have to be set
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
            # replica_head_out = pod.replicas_args['head'].port_out, # equals
            # replica_tail_in = pod.replicas_args['tail'].port_in, # equals

            for pea in pod.peas:
                if 'head' in pea.name:
                    assert pea.args.port_in == pod.args.port_in
                    assert pea.args.port_out == replica_port_in
                if 'tail' in pea.name:
                    assert pea.args.port_in == replica_port_out
                    assert pea.args.port_out == pod.args.port_out
            if pod.args.replicas > 1:
                for replica in pod.replica_list:
                    validate_ports_replica(
                        replica,
                        replica_port_in,
                        replica_port_out,
                        getattr(pod.args, 'parallel', 1),
                    )
        assert pod


def test_use_before_use_after():
    pass


def test_gateway():
    pass


def test_flow_plot():
    pass


def test_workspace_configuration():
    pass
