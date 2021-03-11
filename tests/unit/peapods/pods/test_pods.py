import os

import pytest

from jina.parsers import set_gateway_parser
from jina.parsers import set_pod_parser
from jina.peapods import Pod
from jina.peapods.pods import BasePod


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


@pytest.mark.parametrize(
    'peas_hosts, parallel',
    [
        ('k1: v1', 1),  # test pea_host has value, while it's a singleton pod
        ('1: "0.0.0.2"', 2),  # test 1 pea host set, another pea host not set
        ('1: "0.0.0.2", 2: "0.0.0.3"', 2),  # test all pea host set. should be identical to pod host
    ],
)
def test_pod_remote_pea_parallel(peas_hosts, parallel):
    args = set_pod_parser().parse_args(
        ['--peas-hosts', peas_hosts, peas_hosts, '--parallel', str(parallel)]
    )
    with Pod(args) as pod:
        peas = pod.peas
        for pea in peas:
            if parallel == 1:
                assert pea.args.host == pod.host
            else:
                assert pea.args.host == peas_hosts.get(pea.pea_id, pod.host)

    Pod(args).start().close()
