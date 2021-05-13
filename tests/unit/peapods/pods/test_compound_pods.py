import pytest

from jina.parsers import set_pod_parser
from jina.peapods import CompoundPod
from jina import __default_executor__


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
        assert pod.host_in == '0.0.0.0'
        assert pod.host_out == '0.0.0.0'


def test_address_in_out(pod_args):
    with CompoundPod(pod_args) as pod:
        assert pod.host in pod.address_in
        assert pod.host in pod.address_out


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

        assert bp.replicas[0].name == 'pod/0'
        assert bp.replicas[0].peas[0].name == 'pod/0/head'
        assert bp.replicas[0].peas[0].inner is False
        assert bp.replicas[0].peas[1].name == 'pod/0/0'
        assert bp.replicas[0].peas[1].inner
        assert bp.replicas[0].peas[2].name == 'pod/0/1'
        assert bp.replicas[0].peas[2].inner
        assert bp.replicas[0].peas[3].name == 'pod/0/tail'
        assert bp.replicas[0].peas[3].inner is False

        assert bp.replicas[1].name == 'pod/1'
        assert bp.replicas[1].peas[0].name == 'pod/1/head'
        assert bp.replicas[1].peas[0].inner is False
        assert bp.replicas[1].peas[1].name == 'pod/1/0'
        assert bp.replicas[1].peas[1].inner
        assert bp.replicas[1].peas[2].name == 'pod/1/1'
        assert bp.replicas[1].peas[2].inner
        assert bp.replicas[1].peas[3].name == 'pod/1/tail'
        assert bp.replicas[1].peas[3].inner is False

        assert bp.replicas[2].name == 'pod/2'
        assert bp.replicas[2].peas[0].name == 'pod/2/head'
        assert bp.replicas[2].peas[0].inner is False
        assert bp.replicas[2].peas[1].name == 'pod/2/0'
        assert bp.replicas[2].peas[1].inner
        assert bp.replicas[2].peas[2].name == 'pod/2/1'
        assert bp.replicas[2].peas[2].inner
        assert bp.replicas[2].peas[3].name == 'pod/2/tail'
        assert bp.replicas[2].peas[3].inner is False

        # runtime
        assert bp.head_pea.runtime.name == 'pod/head/ZEDRuntime'
        assert bp.tail_pea.runtime.name == 'pod/tail/ZEDRuntime'

        assert bp.replicas[0].peas[0].runtime.name == 'pod/0/head/ZEDRuntime'
        assert bp.replicas[0].peas[1].runtime.name == 'pod/0/0/ZEDRuntime'
        assert bp.replicas[0].peas[2].runtime.name == 'pod/0/1/ZEDRuntime'
        assert bp.replicas[0].peas[3].runtime.name == 'pod/0/tail/ZEDRuntime'

        assert bp.replicas[1].peas[0].runtime.name == 'pod/1/head/ZEDRuntime'
        assert bp.replicas[1].peas[1].runtime.name == 'pod/1/0/ZEDRuntime'
        assert bp.replicas[1].peas[2].runtime.name == 'pod/1/1/ZEDRuntime'
        assert bp.replicas[1].peas[3].runtime.name == 'pod/1/tail/ZEDRuntime'

        assert bp.replicas[2].peas[0].runtime.name == 'pod/2/head/ZEDRuntime'
        assert bp.replicas[2].peas[1].runtime.name == 'pod/2/0/ZEDRuntime'
        assert bp.replicas[2].peas[2].runtime.name == 'pod/2/1/ZEDRuntime'
        assert bp.replicas[2].peas[3].runtime.name == 'pod/2/tail/ZEDRuntime'


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
            *[f'0.0.0.{i+1}' for i in range(num_hosts)],
            '--runtime-backend',
            'process',
        ]
    )
    compound_pod = CompoundPod(args)
    replica_args = compound_pod.replicas_args
    assert replica_args[0].peas_hosts == used_hosts[0]
    assert replica_args[1].peas_hosts == used_hosts[1]
    assert replica_args[2].peas_hosts == used_hosts[2]
