import os

import pytest

from jina.parsers import set_gateway_parser
from jina.parsers import set_pod_parser
from jina.peapods import Pod
from jina.peapods.pods import BasePod
from jina.peapods.pods.helper import get_public_ip, get_internal_ip


@pytest.mark.parametrize('parallel', [1, 2, 4])
@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_pod_context_parallel(runtime, parallel):
    args = set_pod_parser().parse_args(
        ['--runtime-backend', runtime, '--parallel', str(parallel)]
    )
    with Pod(args) as bp:
        if parallel == 1:
            assert bp.num_peas == 1
        else:
            # count head and tail
            assert bp.num_peas == parallel + 2

    Pod(args).start().close()


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='for unknown reason, this test is flaky on Github action, '
    'but locally it SHOULD work fine',
)
@pytest.mark.parametrize('restful', [True, False])
@pytest.mark.parametrize('runtime', ['process', 'thread'])
@pytest.mark.parametrize('runtime_cls', ['RESTRuntime', 'GRPCRuntime'])
def test_gateway_pod(runtime, restful, runtime_cls):
    args = set_gateway_parser().parse_args(
        ['--runtime-backend', runtime, '--runtime-cls', runtime_cls]
        + (['--restful'] if restful else [])
    )
    with Pod(args) as p:
        assert len(p.all_args) == 1
        if restful:
            assert p.all_args[0].runtime_cls == 'RESTRuntime'
        else:
            assert p.all_args[0].runtime_cls == 'GRPCRuntime'

    Pod(args).start().close()


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_pod_naming_with_parallel(runtime):
    args = set_pod_parser().parse_args(
        ['--name', 'pod', '--parallel', '2', '--runtime-backend', runtime]
    )
    with BasePod(args) as bp:
        assert bp.peas[0].name == 'pod/head'
        assert bp.peas[1].name == 'pod/tail'
        assert bp.peas[2].name == 'pod/1'
        assert bp.peas[3].name == 'pod/2'
        assert bp.peas[0].runtime.name == 'pod/head/ZEDRuntime'
        assert bp.peas[1].runtime.name == 'pod/tail/ZEDRuntime'
        assert bp.peas[2].runtime.name == 'pod/1/ZEDRuntime'
        assert bp.peas[3].runtime.name == 'pod/2/ZEDRuntime'


def test_pod_args_remove_uses_ba():
    args = set_pod_parser().parse_args([])
    with Pod(args) as p:
        assert p.num_peas == 1

    args = set_pod_parser().parse_args(
        ['--uses-before', '_pass', '--uses-after', '_pass']
    )
    with Pod(args) as p:
        assert p.num_peas == 1

    args = set_pod_parser().parse_args(
        ['--uses-before', '_pass', '--uses-after', '_pass', '--parallel', '2']
    )
    with Pod(args) as p:
        assert p.num_peas == 4


# @pytest.mark.parametrize(
#     'peas_hosts, parallel',
#     [
#
#         ('1: 0.0.0.2', 2),  # test 1 pea host set, another pea host not set
#         ('1: 0.0.0.2, 2: 0.0.0.3', 2),  # test all pea host set
#     ],
# )
def test_pod_remote_pea_without_parallel():
    args = set_pod_parser().parse_args(
        ['--peas-hosts', '1: 0.0.0.1', '--parallel', str(1)]
    )
    with Pod(args) as pod:
        peas = pod.peas
        for pea in peas:
            assert pea.args.host == pod.host


@pytest.mark.parametrize(
    'pod_host, pea1_host, expected_host_in, expected_host_out',
    [
        ('0.0.0.0', '0.0.0.1', get_internal_ip(), get_internal_ip()),
        ('0.0.0.1', '0.0.0.2', '0.0.0.1', '0.0.0.1'),
        ('0.0.0.1', '0.0.0.0', '0.0.0.1', '0.0.0.1'),
    ],
)
def test_pod_remote_pea_parallel_pea_host_set_partially(
    pod_host,
    pea1_host,
    expected_host_in,
    expected_host_out,
):
    args = set_pod_parser().parse_args(
        ['--peas-hosts', f'1: {pea1_host}', '--parallel', str(2), '--host', pod_host]
    )
    assert args.host == pod_host
    pod = Pod(args)
    for k, v in pod.peas_args.items():
        if k in ['head', 'tail']:
            assert v.host == args.host
        else:
            for pea_arg in v:
                if pea_arg.pea_id == 1:
                    assert pea_arg.host == pea1_host
                    assert pea_arg.host_in == expected_host_in
                    assert pea_arg.host_out == expected_host_out
                else:
                    assert pea_arg.host == args.host
                    assert pea_arg.host_in == '0.0.0.0'
                    assert pea_arg.host_out == '0.0.0.0'


@pytest.mark.parametrize(
    'pod_host, peas_hosts, expected_host_in, expected_host_out',
    [
        ('0.0.0.0', ['0.0.0.1', '0.0.0.2'], get_internal_ip(), get_internal_ip()),
        ('0.0.0.1', ['0.0.0.2', '0.0.0.3'], '0.0.0.1', '0.0.0.1'),
        ('0.0.0.1', ['0.0.0.0', '0.0.0.2'], '0.0.0.1', '0.0.0.1'),
    ],
)
def test_pod_remote_pea_parallel_pea_host_set_completely(
    pod_host,
    peas_hosts,
    expected_host_in,
    expected_host_out,
):
    args = set_pod_parser().parse_args(
        [
            '--peas-hosts',
            f'1: {peas_hosts[0]}',
            f'2: {peas_hosts[1]}',
            '--parallel',
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
