import os

import pytest

from jina.helper import get_internal_ip
from jina.parsers import set_gateway_parser
from jina.parsers import set_pod_parser
from jina.peapods import Pod
from jina import __default_executor__, __default_host__

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='function')
def pod_args():
    args = [
        '--name',
        'test',
        '--replicas',
        '2',
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
        '--replicas',
        '1',
        '--host',
        __default_host__,
    ]
    return set_pod_parser().parse_args(args)


def test_name(pod_args):
    with Pod(pod_args) as pod:
        assert pod.name == 'test'


def test_host(pod_args):
    with Pod(pod_args) as pod:
        assert pod.host == __default_host__
        assert pod.head_host == __default_host__


def test_is_ready(pod_args):
    with Pod(pod_args) as pod:
        assert pod.is_ready is True


def test_equal(pod_args, pod_args_singleton):
    pod1 = Pod(pod_args)
    pod2 = Pod(pod_args)
    assert pod1 == pod2
    pod1.close()
    pod2.close()
    # test not equal
    pod1 = Pod(pod_args)
    pod2 = Pod(pod_args_singleton)
    assert pod1 != pod2
    pod1.close()
    pod2.close()


def test_head_args_get_set(pod_args, pod_args_singleton):
    with Pod(pod_args) as pod:
        assert pod.head_args == pod.peas_args['head']
        pod.head_args = pod_args_singleton
        assert pod.peas_args['head'] == pod_args_singleton

    with Pod(pod_args_singleton) as pod:
        assert pod.head_args == pod.first_pea_args
        pod.head_args = pod_args
        assert pod.peas_args['peas'][0] == pod_args


def test_tail_args_get_set(pod_args, pod_args_singleton):
    with Pod(pod_args) as pod:
        assert pod.tail_args == pod.peas_args['tail']
        pod.tail_args = pod_args_singleton
        assert pod.peas_args['tail'] == pod_args_singleton

    with Pod(pod_args_singleton) as pod:
        assert pod.tail_args == pod.first_pea_args
        pod.tail_args = pod_args
        assert pod.peas_args['peas'][0] == pod_args


@pytest.mark.slow
@pytest.mark.parametrize('replicas', [1, 2, 4])
@pytest.mark.parametrize('runtime', ['process', 'thread'])
@pytest.mark.parametrize('grpc_data_requests', [False, True])
def test_pod_context_replicas(runtime, replicas, grpc_data_requests):
    args_list = ['--runtime-backend', runtime, '--replicas', str(replicas)]
    if grpc_data_requests:
        args_list.append('--grpc-data-requests')
    args = set_pod_parser().parse_args(args_list)
    with Pod(args) as bp:
        if replicas == 1:
            assert bp.num_peas == 1
        else:
            # count head and tail
            assert bp.num_peas == replicas + 2

    Pod(args).start().close()


@pytest.mark.slow
@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='for unknown reason, this test is flaky on Github action, '
    'but locally it SHOULD work fine',
)
@pytest.mark.parametrize('runtime', ['process', 'thread'])
@pytest.mark.parametrize(
    'protocol, runtime_cls',
    [
        ('grpc', 'GRPCRuntime'),
    ],
)
def test_gateway_pod(runtime, protocol, runtime_cls):
    args = set_gateway_parser().parse_args(
        ['--runtime-backend', runtime, '--protocol', protocol]
    )
    with Pod(args) as p:
        assert len(p.all_args) == 1
        assert p.all_args[0].runtime_cls == runtime_cls

    Pod(args).start().close()


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_pod_naming_with_replica(runtime):
    args = set_pod_parser().parse_args(
        ['--name', 'pod', '--replicas', '2', '--runtime-backend', runtime]
    )
    with Pod(args) as bp:
        assert bp.head_pea.name == 'pod/head'
        assert bp.replica_set._peas[0].name == 'pod/rep-0'
        assert bp.replica_set._peas[1].name == 'pod/rep-1'
        assert bp.tail_pea.name == 'pod/tail'


def test_pod_args_remove_uses_ba():
    args = set_pod_parser().parse_args([])
    with Pod(args) as p:
        assert p.num_peas == 1

    args = set_pod_parser().parse_args(
        ['--uses-before', __default_executor__, '--uses-after', __default_executor__]
    )
    with Pod(args) as p:
        assert p.num_peas == 1

    args = set_pod_parser().parse_args(
        [
            '--uses-before',
            __default_executor__,
            '--uses-after',
            __default_executor__,
            '--replicas',
            '2',
        ]
    )
    with Pod(args) as p:
        assert p.num_peas == 4


def test_pod_remote_pea_without_replicas():
    args = set_pod_parser().parse_args(
        ['--peas-hosts', '0.0.0.1', '--replicas', str(1)]
    )
    with Pod(args) as pod:
        pea = pod.replica_set._peas[0]
        assert pea.args.host == pod.host


@pytest.mark.parametrize(
    'pod_host, pea1_host, expected_host_in, expected_host_out',
    [
        (__default_host__, '0.0.0.1', get_internal_ip(), get_internal_ip()),
        ('0.0.0.1', '0.0.0.2', '0.0.0.1', '0.0.0.1'),
        ('0.0.0.1', __default_host__, '0.0.0.1', '0.0.0.1'),
    ],
)
def test_pod_remote_pea_replicas_pea_host_set_partially(
    pod_host,
    pea1_host,
    expected_host_in,
    expected_host_out,
):
    args = set_pod_parser().parse_args(
        ['--peas-hosts', f'{pea1_host}', '--replicas', str(2), '--host', pod_host]
    )
    assert args.host == pod_host
    pod = Pod(args)
    for k, v in pod.peas_args.items():
        if k in ['head', 'tail']:
            assert v.host == args.host
        else:
            for pea_arg in v:
                if pea_arg.pea_id in (0, 1):
                    assert pea_arg.host == pea1_host
                    assert pea_arg.host_in == expected_host_in
                    assert pea_arg.host_out == expected_host_out
                else:
                    assert pea_arg.host == args.host
                    assert pea_arg.host_in == __default_host__
                    assert pea_arg.host_out == __default_host__


@pytest.mark.parametrize(
    'pod_host, peas_hosts, expected_host_in, expected_host_out',
    [
        (
            __default_host__,
            ['0.0.0.1', '0.0.0.2'],
            get_internal_ip(),
            get_internal_ip(),
        ),
        ('0.0.0.1', ['0.0.0.2', '0.0.0.3'], '0.0.0.1', '0.0.0.1'),
        ('0.0.0.1', [__default_host__, '0.0.0.2'], '0.0.0.1', '0.0.0.1'),
    ],
)
def test_pod_remote_pea_replicas_pea_host_set_completely(
    pod_host,
    peas_hosts,
    expected_host_in,
    expected_host_out,
):
    args = set_pod_parser().parse_args(
        [
            '--peas-hosts',
            f'{peas_hosts[0]}',
            f'{peas_hosts[1]}',
            '--replicas',
            str(2),
            '--host',
            pod_host,
        ]
    )
    assert args.host == pod_host
    pod = Pod(args)
    for k, v in pod.peas_args.items():
        if k in ['head', 'tail']:
            assert v.host == args.host
        else:
            for pea_arg, pea_host in zip(v, peas_hosts):
                assert pea_arg.host == pea_host
                assert pea_arg.host_in == expected_host_in
                assert pea_arg.host_out == expected_host_out


@pytest.mark.parametrize('replicas', [1])
@pytest.mark.parametrize(
    'upload_files',
    [[os.path.join(cur_dir, __file__), os.path.join(cur_dir, '__init__.py')]],
)
@pytest.mark.parametrize(
    'uses, uses_before, uses_after, py_modules, expected',
    [
        (
            os.path.join(cur_dir, '../../yaml/dummy_ext_exec.yml'),
            '',
            '',
            [
                os.path.join(cur_dir, '../../yaml/dummy_exec.py'),
                os.path.join(cur_dir, '__init__.py'),
            ],
            [
                os.path.join(cur_dir, '../../yaml/dummy_ext_exec.yml'),
                os.path.join(cur_dir, '../../yaml/dummy_exec.py'),
                os.path.join(cur_dir, __file__),
                os.path.join(cur_dir, '__init__.py'),
            ],
        ),
        (
            os.path.join(cur_dir, '../../yaml/dummy_ext_exec.yml'),
            os.path.join(cur_dir, '../../yaml/dummy_exec.py'),
            os.path.join(cur_dir, '../../yaml/dummy_ext_exec.yml'),
            [
                os.path.join(cur_dir, '../../yaml/dummy_exec.py'),
                os.path.join(cur_dir, '../../yaml/dummy_ext_exec.yml'),
            ],
            [
                os.path.join(cur_dir, '../../yaml/dummy_ext_exec.yml'),
                os.path.join(cur_dir, '../../yaml/dummy_exec.py'),
                os.path.join(cur_dir, __file__),
                os.path.join(cur_dir, '__init__.py'),
            ],
        ),
        (
            'non_existing1.yml',
            'non_existing3.yml',
            'non_existing4.yml',
            ['non_existing1.py', 'non_existing2.py'],
            [os.path.join(cur_dir, __file__), os.path.join(cur_dir, '__init__.py')],
        ),
    ],
)
def test_pod_upload_files(
    replicas,
    upload_files,
    uses,
    uses_before,
    uses_after,
    py_modules,
    expected,
):
    args = set_pod_parser().parse_args(
        [
            '--uses',
            uses,
            '--uses-before',
            uses_before,
            '--uses-after',
            uses_after,
            '--py-modules',
            *py_modules,
            '--upload-files',
            *upload_files,
            '--replicas',
            str(replicas),
        ]
    )
    pod = Pod(args)
    for k, v in pod.peas_args.items():
        if k in ['head', 'tail']:
            if v:
                pass
                # assert sorted(v.upload_files) == sorted(expected)
        else:
            for pea in v:
                print(sorted(pea.upload_files))
                print(sorted(expected))
                assert sorted(pea.upload_files) == sorted(expected)
