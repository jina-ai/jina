import pytest

from jina.enums import SchedulerType, SocketType, PollingType
from jina.parsers import set_pod_parser
from jina import __default_executor__, __default_host__
from jina.peapods import CompoundPod, Pod


@pytest.fixture(scope='function')
def pod_args():
    args = [
        '--name',
        'test',
        '--shards',
        '2',
        '--replicas',
        '3',
        '--host',
        __default_host__,
    ]
    return set_pod_parser().parse_args(args)


@pytest.fixture(scope='function')
def pod_args_singleton():
    args = [
        '--name',
        'test2',
        '--uses-before',
        __default_executor__,
        '--shards',
        '1',
        '--replicas',
        '3',
        '--host',
        __default_host__,
    ]
    return set_pod_parser().parse_args(args)


def test_name(pod_args):
    with CompoundPod(pod_args) as pod:
        assert pod.name == 'test'


def test_host(pod_args):
    with CompoundPod(pod_args) as pod:
        assert pod.host == __default_host__
        assert pod.head_host == __default_host__


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


@pytest.mark.slow
@pytest.mark.parametrize('shards', [2, 4])
@pytest.mark.parametrize('replicas', [3, 1])
@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_pod_context_sharded(runtime, shards, replicas):
    args = set_pod_parser().parse_args(
        [
            '--runtime-backend',
            runtime,
            '--shards',
            str(shards),
            '--replicas',
            str(replicas),
        ]
    )
    with CompoundPod(args) as bp:
        if replicas == 1:
            assert bp.num_peas == shards + 2
        else:
            # count head and tail
            assert bp.num_peas == shards * (replicas + 2) + 2

    with CompoundPod(args):
        pass


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_pod_naming_with_shards(runtime):
    args = set_pod_parser().parse_args(
        [
            '--name',
            'pod',
            '--shards',
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

        assert bp.shards[0].name == 'pod/shard-0'
        assert bp.shards[0].head_pea.name == 'pod/shard-0/head'
        assert bp.shards[0].head_pea._is_inner_pea is False
        assert bp.shards[0].replica_set._peas[0].name == 'pod/shard-0/rep-0'
        assert bp.shards[0].replica_set._peas[0]._is_inner_pea
        assert bp.shards[0].replica_set._peas[1].name == 'pod/shard-0/rep-1'
        assert bp.shards[0].replica_set._peas[1]._is_inner_pea
        assert bp.shards[0].replica_set._peas[2].name == 'pod/shard-0/rep-2'
        assert bp.shards[0].replica_set._peas[2]._is_inner_pea
        assert bp.shards[0].tail_pea.name == 'pod/shard-0/tail'
        assert bp.shards[0].tail_pea._is_inner_pea is False

        assert bp.shards[1].name == 'pod/shard-1'
        assert bp.shards[1].head_pea.name == 'pod/shard-1/head'
        assert bp.shards[1].head_pea._is_inner_pea is False
        assert bp.shards[1].replica_set._peas[0].name == 'pod/shard-1/rep-0'
        assert bp.shards[1].replica_set._peas[0]._is_inner_pea
        assert bp.shards[1].replica_set._peas[1].name == 'pod/shard-1/rep-1'
        assert bp.shards[1].replica_set._peas[1]._is_inner_pea
        assert bp.shards[1].replica_set._peas[2].name == 'pod/shard-1/rep-2'
        assert bp.shards[1].replica_set._peas[2]._is_inner_pea
        assert bp.shards[1].tail_pea.name == 'pod/shard-1/tail'
        assert bp.shards[1].tail_pea._is_inner_pea is False


@pytest.mark.parametrize(
    'num_hosts, used_hosts',
    (
        (
            6,
            (
                ['0.0.0.1', '0.0.0.2', '0.0.0.3'],
                ['0.0.0.4', '0.0.0.5', '0.0.0.6'],
            ),
        ),
        (
            8,
            (
                ['0.0.0.1', '0.0.0.2', '0.0.0.3'],
                ['0.0.0.4', '0.0.0.5', '0.0.0.6'],
            ),
        ),
        (
            3,
            (
                ['0.0.0.1', '0.0.0.2', '0.0.0.3'],
                ['0.0.0.1', '0.0.0.2', '0.0.0.3'],
            ),
        ),
    ),
)
def test_host_list_matching(num_hosts, used_hosts):
    args = set_pod_parser().parse_args(
        [
            '--name',
            'pod',
            '--shards',
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
    shard_args = compound_pod.shards_args
    assert shard_args[0].peas_hosts == used_hosts[0]
    assert shard_args[1].peas_hosts == used_hosts[1]


@pytest.mark.parametrize(
    'polling, shards, pea_socket_in',
    (
        (
            'all',
            1,
            SocketType.SUB_CONNECT,
        ),
        (
            'all',
            2,
            SocketType.SUB_CONNECT,
        ),
        (
            'any',
            2,
            SocketType.DEALER_CONNECT,
        ),
    ),
)
def test_sockets(polling, shards, pea_socket_in):
    polling_type = PollingType.ALL if polling == 'all' else PollingType.ANY
    args = set_pod_parser().parse_args(
        [
            '--name',
            'pod',
            '--shards',
            f'{shards}',
            '--polling',
            f'{polling}',
            '--replicas',
            '3',
        ]
    )

    with CompoundPod(args) as compound_pod:
        head = compound_pod.head_args
        tail = compound_pod.tail_args

        assert compound_pod.args.polling == polling_type
        assert head.socket_in == SocketType.ROUTER_BIND
        if polling_type == PollingType.ANY:
            assert head.socket_out == SocketType.ROUTER_BIND
            assert tail.num_part == 1
        else:
            assert head.socket_out == SocketType.PUB_BIND
            assert tail.num_part == shards
        assert head.scheduling == SchedulerType.LOAD_BALANCE

        assert tail.socket_in == SocketType.PULL_BIND
        assert tail.socket_out == SocketType.ROUTER_BIND
        assert tail.scheduling == SchedulerType.LOAD_BALANCE

        pod_shards = compound_pod.shards
        for shard in pod_shards:
            assert shard.num_peas == 5

            assert shard.head_args.socket_in == pea_socket_in
            assert shard.head_args.socket_out == SocketType.ROUTER_BIND

            assert shard.tail_args.socket_in == SocketType.PULL_BIND
            assert shard.tail_args.socket_out == SocketType.PUSH_CONNECT

            for pea in shard.peas_args['peas']:
                assert pea.socket_in == SocketType.DEALER_CONNECT
                assert pea.socket_out == SocketType.PUSH_CONNECT


def test_compound_pod_do_not_forward_uses_before_uses_after():
    polling = 'all'
    shards = 2
    replicas = 2
    args = set_pod_parser().parse_args(
        [
            '--name',
            'pod',
            '--shards',
            f'{shards}',
            '--polling',
            f'{polling}',
            '--replicas',
            f'{replicas}',
            '--uses-after',
            'BaseExecutor',
            '--uses-before',
            'BaseExecutor',
        ]
    )

    cpod = CompoundPod(args)
    for pod in cpod.shards:
        assert pod.args.uses_before is None
        assert pod.args.uses_after is None
