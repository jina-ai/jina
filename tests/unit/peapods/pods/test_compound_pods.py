import pytest

from jina.parsers import set_pod_parser
from jina.peapods import CompoundPod


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
        '_pass',
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


def test_head_args_get_set(pod_args):
    with CompoundPod(pod_args) as pod:
        assert pod.head_args == pod.replicas_args['head']


def test_tail_args_get_set(pod_args):
    with CompoundPod(pod_args) as pod:
        assert pod.tail_args == pod.replicas_args['tail']


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
        assert bp.peas[0].name == 'pod/head'
        assert bp.peas[1].name == 'pod/tail'

        assert bp.replica_list[0].name == 'pod/0'
        assert bp.replica_list[0].peas[0].name == 'pod/0/head'
        assert bp.replica_list[0].peas[1].name == 'pod/0/tail'
        assert bp.replica_list[0].peas[2].name == 'pod/0/0'
        assert bp.replica_list[0].peas[3].name == 'pod/0/1'

        assert bp.replica_list[1].name == 'pod/1'
        assert bp.replica_list[1].peas[0].name == 'pod/1/head'
        assert bp.replica_list[1].peas[1].name == 'pod/1/tail'
        assert bp.replica_list[1].peas[2].name == 'pod/1/0'
        assert bp.replica_list[1].peas[3].name == 'pod/1/1'

        assert bp.replica_list[2].name == 'pod/2'
        assert bp.replica_list[2].peas[0].name == 'pod/2/head'
        assert bp.replica_list[2].peas[1].name == 'pod/2/tail'
        assert bp.replica_list[2].peas[2].name == 'pod/2/0'
        assert bp.replica_list[2].peas[3].name == 'pod/2/1'

        # runtime
        assert bp.peas[0].runtime.name == 'pod/head/ZEDRuntime'
        assert bp.peas[1].runtime.name == 'pod/tail/ZEDRuntime'

        assert bp.replica_list[0].peas[0].runtime.name == 'pod/0/head/ZEDRuntime'
        assert bp.replica_list[0].peas[1].runtime.name == 'pod/0/tail/ZEDRuntime'
        assert bp.replica_list[0].peas[2].runtime.name == 'pod/0/0/ZEDRuntime'
        assert bp.replica_list[0].peas[3].runtime.name == 'pod/0/1/ZEDRuntime'

        assert bp.replica_list[1].peas[0].runtime.name == 'pod/1/head/ZEDRuntime'
        assert bp.replica_list[1].peas[1].runtime.name == 'pod/1/tail/ZEDRuntime'
        assert bp.replica_list[1].peas[2].runtime.name == 'pod/1/0/ZEDRuntime'
        assert bp.replica_list[1].peas[3].runtime.name == 'pod/1/1/ZEDRuntime'

        assert bp.replica_list[2].peas[0].runtime.name == 'pod/2/head/ZEDRuntime'
        assert bp.replica_list[2].peas[1].runtime.name == 'pod/2/tail/ZEDRuntime'
        assert bp.replica_list[2].peas[2].runtime.name == 'pod/2/0/ZEDRuntime'
        assert bp.replica_list[2].peas[3].runtime.name == 'pod/2/1/ZEDRuntime'
