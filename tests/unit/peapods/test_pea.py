import pytest

from jina.excepts import PeaFailToStart
from jina.parser import set_pea_parser, set_pod_parser, set_gateway_parser
from jina.peapods.gateway import GatewayPea
from jina.peapods.pea import BasePea
from jina.peapods.pod import BasePod


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_pea_context(runtime):
    args = set_pea_parser().parse_args(['--runtime', runtime])
    with BasePea(args):
        pass

    BasePea(args).start().close()


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_gateway_pea(runtime):
    args = set_gateway_parser().parse_args(['--runtime', runtime])
    with GatewayPea(args):
        pass
    GatewayPea(args).start().close()


def test_address_in_use():
    with pytest.raises(PeaFailToStart):
        args1 = set_pea_parser().parse_args(['--port-ctrl', '55555'])
        args2 = set_pea_parser().parse_args(['--port-ctrl', '55555'])
        with BasePea(args1), BasePea(args2):
            pass

    with pytest.raises(PeaFailToStart):
        args1 = set_pea_parser().parse_args(['--port-ctrl', '55555', '--runtime', 'thread'])
        args2 = set_pea_parser().parse_args(['--port-ctrl', '55555', '--runtime', 'thread'])
        with BasePea(args1), BasePea(args2):
            pass


def test_peas_naming_with_parallel():
    args = set_pod_parser().parse_args(['--name', 'pod',
                                        '--parallel', '2',
                                        '--max-idle-time', '5',
                                        '--shutdown-idle'])
    with BasePod(args) as bp:
        assert bp.peas[0].name == 'pod-head'
        assert bp.peas[1].name == 'pod-tail'
        assert bp.peas[2].name == 'pod-1'
        assert bp.peas[3].name == 'pod-2'
