import pytest

from jina.excepts import PeaFailToStart
from jina.parser import set_pea_parser, set_pod_parser, set_gateway_parser
from jina.peapods.runtimes.local import LocalRuntime
from jina.peapods.pods import BasePod


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_local_runtime_context(runtime):
    args = set_pea_parser().parse_args(['--runtime', runtime])
    with LocalRuntime(args):
        pass

    LocalRuntime(args).start().close()


@pytest.mark.parametrize('rest_api', [False, True])
@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_gateway_runtime(runtime, rest_api):
    args = set_gateway_parser().parse_args(['--runtime', runtime])
    with LocalRuntime(args, gateway=True, rest_api=rest_api):
        pass

    LocalRuntime(args, gateway=True, rest_api=False).start().close()


def test_address_in_use():
    with pytest.raises(PeaFailToStart):
        args1 = set_pea_parser().parse_args(['--port-ctrl', '55555'])
        args2 = set_pea_parser().parse_args(['--port-ctrl', '55555'])
        with LocalRuntime(args1), LocalRuntime(args2):
            pass

    with pytest.raises(PeaFailToStart):
        args1 = set_pea_parser().parse_args(['--port-ctrl', '55555', '--runtime', 'thread'])
        args2 = set_pea_parser().parse_args(['--port-ctrl', '55555', '--runtime', 'thread'])
        with LocalRuntime(args1), LocalRuntime(args2):
            pass


def test_local_runtime_naming_with_parallel():
    args = set_pod_parser().parse_args(['--name', 'pod',
                                        '--parallel', '2',
                                        '--max-idle-time', '5',
                                        '--shutdown-idle'])
    with BasePod(args) as bp:
        assert bp.runtimes[0].name == 'runtime-pod-head'
        assert bp.runtimes[1].name == 'runtime-pod-tail'
        assert bp.runtimes[2].name == 'runtime-pod-1'
        assert bp.runtimes[3].name == 'runtime-pod-2'
        assert bp.runtimes[0].pea.name == 'pod-head'
        assert bp.runtimes[1].pea.name == 'pod-tail'
        assert bp.runtimes[2].pea.name == 'pod-1'
        assert bp.runtimes[3].pea.name == 'pod-2'
