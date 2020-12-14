import pytest

from jina.excepts import PeaFailToStart
from jina.parser import set_pea_parser, set_pod_parser, set_gateway_parser
from jina.peapods.runtimes.local import LocalRunTime
from jina.peapods.pods import BasePod


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_pea_context(runtime):
    args = set_pea_parser().parse_args(['--runtime', runtime])
    with LocalRunTime(args):
        pass

    LocalRunTime(args).start().close()


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_gateway_pea(runtime):
    args = set_gateway_parser().parse_args(['--runtime', runtime])
    with LocalRunTime(args, gateway=True, rest_api=False):
        pass

    LocalRunTime(args, gateway=True, rest_api=False).start().close()


# TODO: This will be fixed once the `set_ready` is properly set in runtime
def test_address_in_use():
    with pytest.raises(PeaFailToStart):
        args1 = set_pea_parser().parse_args(['--port-ctrl', '55555'])
        args2 = set_pea_parser().parse_args(['--port-ctrl', '55555'])
        with LocalRunTime(args1), LocalRunTime(args2):
            pass

    with pytest.raises(PeaFailToStart):
        args1 = set_pea_parser().parse_args(['--port-ctrl', '55555', '--runtime', 'thread'])
        args2 = set_pea_parser().parse_args(['--port-ctrl', '55555', '--runtime', 'thread'])
        with LocalRunTime(args1), LocalRunTime(args2):
            pass


def test_peas_naming_with_parallel():
    args = set_pod_parser().parse_args(['--name', 'pod',
                                        '--parallel', '2',
                                        '--max-idle-time', '5',
                                        '--shutdown-idle'])
    with BasePod(args) as bp:
        assert bp.runtimes[0].name == 'support-pod-head'
        assert bp.runtimes[1].name == 'support-pod-tail'
        assert bp.runtimes[2].name == 'support-pod-1'
        assert bp.runtimes[3].name == 'support-pod-2'
        assert bp.runtimes[0].pea.name == 'pod-head'
        assert bp.runtimes[1].pea.name == 'pod-tail'
        assert bp.runtimes[2].pea.name == 'pod-1'
        assert bp.runtimes[3].pea.name == 'pod-2'
