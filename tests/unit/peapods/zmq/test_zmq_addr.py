import pytest

from jina.peapods.zmq import Zmqlet


@pytest.mark.parametrize('host', ['pi@192.0.0.1', '192.0.0.1'])
def test_get_ctrl_addr(host):
    assert Zmqlet.get_ctrl_address(host, 56789, False)[0] == 'tcp://192.0.0.1:56789'


@pytest.mark.parametrize('host', ['pi@192.0.0.1', '192.0.0.1'])
def test_get_ctrl_addr_ipc(host):
    assert 'ipc' == Zmqlet.get_ctrl_address(host, 56789, True)[0][0:3]
