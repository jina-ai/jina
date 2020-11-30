import pytest

from jina.parser import set_pod_parser, set_gateway_parser
from jina.peapods.gateway import GatewayPea
from jina.peapods.pod import BasePod


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_gateway_pea(runtime):
    args = set_gateway_parser().parse_args(['--runtime', runtime])
    with GatewayPea(args):
        pass
    GatewayPea(args).start().close()


def test_peas_naming_with_parallel():
    args = set_pod_parser().parse_args(['--name', 'pod',
                                        '--parallel', '2',
                                        '--max-idle-time', '5',
                                        '--shutdown-idle'])
    with BasePod(args) as bp:
        assert bp.pea_runtimes[0].pea.name == 'pod-head'
        assert bp.pea_runtimes[1].pea.name == 'pod-tail'
        assert bp.pea_runtimes[2].pea.name == 'pod-1'
        assert bp.pea_runtimes[3].pea.name == 'pod-2'
