import pytest

from jina.parser import set_gateway_parser, set_pea_parser
from jina.peapods.pod import GatewayPod

if False:
    from jina.peapods.remote import PeaSpawnHelper


@pytest.mark.skip
def test_remote_not_allowed():
    f_args = set_gateway_parser().parse_args([])
    p_args = set_pea_parser().parse_args(['--host', 'localhost', '--port-expose', str(f_args.port_expose)])
    with GatewayPod(f_args):
        PeaSpawnHelper(p_args).start()


@pytest.mark.skip
@pytest.mark.parametrize('args', [['--allow-spawn'], []])
def test_cont_gateway(args):
    parsed_args = set_gateway_parser().parse_args(args)
    with GatewayPod(parsed_args):
        pass
