import pytest

from jina.enums import SchedulerType, SocketType, PollingType
from jina.parsers import set_pod_parser
from jina import __default_executor__
from jina.peapods import CompoundPod, Pod


@pytest.fixture(scope='function')
def pod_args():
    args = [
        '--name',
        'test',
        '--parallel',
        '2',
        '--replicas',
        '3',
        '--host',
        '0.0.0.0',
    ]
    return set_pod_parser().parse_args(args)


@pytest.fixture(scope='function')
def pod_args_singleton():
    args = [
        '--name',
        'test2',
        '--uses-before',
        __default_executor__,
        '--parallel',
        '1',
        '--replicas',
        '3',
        '--host',
        '0.0.0.0',
    ]
    return set_pod_parser().parse_args(args)


def test_name(pod_args):
    with CompoundPod(pod_args) as pod:
        assert pod.name == 'test'


def test_host(pod_args):
    with CompoundPod(pod_args) as pod:
        assert pod.host == '0.0.0.0'
        assert pod.head_host == '0.0.0.0'


def test_is_ready(pod_args):
    with CompoundPod(pod_args) as pod:
        assert pod.is_ready is True


def test_equal(pod_args, pod_args_singleton):
    pod1 = CompoundPod(pod_args)
    pod2 = CompoundPod(pod_args)
    assert pod1 == pod2
    pod1.close()
    pod2.close()
    # test not equal
    pod1 = CompoundPod(pod_args)
    pod2 = CompoundPod(pod_args_singleton)
    assert pod1 != pod2
    pod1.close()
    pod2.close()


@pytest.mark.parametrize('parallel', [1, 4])
@pytest.mark.parametrize('replicas', [3])
@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_pod_context_parallel(runtime, parallel, replicas):
    args = set_pod_parser().parse_args(
        [
            '--runtime-backend',
            runtime,
            '--parallel',
            str(parallel),
            '--replicas',
            str(replicas),
        ]
    )
    with CompoundPod(args) as bp:
        if parallel == 1:
            assert bp.num_peas == parallel * replicas + 2
        else:
            # count head and tail
            assert bp.num_peas == (parallel + 2) * replicas + 2

    with CompoundPod(args) as pod:
        pass


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_pod_naming_with_parallel(runtime):
    args = set_pod_parser().parse_args(
        [
            '--name',
            'pod',
            '--parallel',
            '2',
            '--replicas',
            '3',
            '--runtime-backend',
            runtime,
        ]
    )
    with CompoundPod(args) as bp:
        assert bp.head_pea.name == 'pod/head'
        assert bp.tail_pea.name == 'pod/tail'

        assert bp.replicas[0].name == 'pod/rep-0'
        assert bp.replicas[0].peas[0].name == 'pod/rep-0/head'
        assert bp.replicas[0].peas[0]._is_inner_pea is False
        assert bp.replicas[0].peas[1].name == 'pod/rep-0/pea-0'
        assert bp.replicas[0].peas[1]._is_inner_pea
        assert bp.replicas[0].peas[2].name == 'pod/rep-0/pea-1'
        assert bp.replicas[0].peas[2]._is_inner_pea
        assert bp.replicas[0].peas[3].name == 'pod/rep-0/tail'
        assert bp.replicas[0].peas[3]._is_inner_pea is False

        assert bp.replicas[1].name == 'pod/rep-1'
        assert bp.replicas[1].peas[0].name == 'pod/rep-1/head'
        assert bp.replicas[1].peas[0]._is_inner_pea is False
        assert bp.replicas[1].peas[1].name == 'pod/rep-1/pea-0'
        assert bp.replicas[1].peas[1]._is_inner_pea
        assert bp.replicas[1].peas[2].name == 'pod/rep-1/pea-1'
        assert bp.replicas[1].peas[2]._is_inner_pea
        assert bp.replicas[1].peas[3].name == 'pod/rep-1/tail'
        assert bp.replicas[1].peas[3]._is_inner_pea is False

        assert bp.replicas[2].name == 'pod/rep-2'
        assert bp.replicas[2].peas[0].name == 'pod/rep-2/head'
        assert bp.replicas[2].peas[0]._is_inner_pea is False
        assert bp.replicas[2].peas[1].name == 'pod/rep-2/pea-0'
        assert bp.replicas[2].peas[1]._is_inner_pea
        assert bp.replicas[2].peas[2].name == 'pod/rep-2/pea-1'
        assert bp.replicas[2].peas[2]._is_inner_pea
        assert bp.replicas[2].peas[3].name == 'pod/rep-2/tail'
        assert bp.replicas[2].peas[3]._is_inner_pea is False


@pytest.mark.parametrize(
    'num_hosts, used_hosts',
    (
        (
            6,
            (
                ['0.0.0.1', '0.0.0.2'],
                ['0.0.0.3', '0.0.0.4'],
                ['0.0.0.5', '0.0.0.6'],
            ),
        ),
        (
            8,
            (
                ['0.0.0.1', '0.0.0.2'],
                ['0.0.0.3', '0.0.0.4'],
                ['0.0.0.5', '0.0.0.6'],
            ),
        ),
        (
            3,
            (
                ['0.0.0.1', '0.0.0.2'],
                ['0.0.0.3', '0.0.0.1'],
                ['0.0.0.2', '0.0.0.3'],
            ),
        ),
    ),
)
def test_host_list_matching(num_hosts, used_hosts):
    args = set_pod_parser().parse_args(
        [
            '--name',
            'pod',
            '--parallel',
            '2',
            '--replicas',
            '3',
            '--peas-hosts',
            *[f'0.0.0.{i + 1}' for i in range(num_hosts)],
            '--runtime-backend',
            'process',
        ]
    )
    compound_pod = CompoundPod(args)
    replica_args = compound_pod.replicas_args
    assert replica_args[0].peas_hosts == used_hosts[0]
    assert replica_args[1].peas_hosts == used_hosts[1]
    assert replica_args[2].peas_hosts == used_hosts[2]


@pytest.mark.parametrize(
    'polling, parallel, pea_scheduling, pea_socket_in, pea_socket_out',
    (
        (
            'all',
            1,
            SchedulerType.LOAD_BALANCE,
            SocketType.DEALER_CONNECT,
            SocketType.PUSH_CONNECT,
        ),
        (
            'all',
            2,
            SchedulerType.LOAD_BALANCE,
            SocketType.SUB_CONNECT,
            SocketType.PUSH_CONNECT,
        ),
        (
            'any',
            2,
            SchedulerType.LOAD_BALANCE,
            SocketType.SUB_CONNECT,
            SocketType.PUSH_CONNECT,
        ),
    ),
)
def test_sockets(polling, parallel, pea_scheduling, pea_socket_in, pea_socket_out):
    polling_type = PollingType.ALL if polling == 'all' else PollingType.ANY
    args = set_pod_parser().parse_args(
        [
            '--name',
            'pod',
            '--parallel',
            f'{parallel}',
            '--polling',
            f'{polling}',
            '--replicas',
            '3',
        ]
    )
    with CompoundPod(args) as compound_pod:
        head = compound_pod.head_args
        assert head.socket_in == SocketType.ROUTER_BIND
        assert head.socket_out == SocketType.ROUTER_BIND
        assert head.scheduling == SchedulerType.LOAD_BALANCE
        tail = compound_pod.tail_args
        assert tail.socket_in == SocketType.PULL_BIND
        assert tail.socket_out == SocketType.DEALER_CONNECT
        assert tail.scheduling == SchedulerType.LOAD_BALANCE
        replicas = compound_pod.replicas
        for replica in replicas:
            if parallel > 1:
                assert len(replica.peas_args['peas']) == parallel
                for pea in replica.peas_args['peas']:
                    assert pea.polling == PollingType.ALL
                    assert pea.socket_in == pea_socket_in
                    assert pea.socket_out == pea_socket_out
                    assert pea.scheduling == pea_scheduling
            else:
                assert len(replica.peas) == 1
                assert replica.peas[0].args.polling == polling_type
                assert replica.peas[0].args.socket_in == pea_socket_in
                assert replica.peas[0].args.socket_out == pea_socket_out
                assert replica.peas[0].args.scheduling == pea_scheduling
