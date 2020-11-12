import pytest

from jina.parser import set_pea_parser
from jina.peapods.zmq import Zmqlet


@pytest.mark.parametrize('host', ['pi@192.0.0.1', '192.0.0.1'])
def test_get_ctrl_addr(host):
    p = set_pea_parser().parse_args(['--host', 'pi@192.0.0.1', '--port-ctrl', '56789'])
    assert Zmqlet.get_ctrl_address(p)[0] == 'tcp://192.0.0.1:56789'
