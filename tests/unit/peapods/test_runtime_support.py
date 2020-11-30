import pytest

from jina.excepts import PeaFailToStart
from jina.parser import set_pea_parser
from jina.peapods.runtime_support import RunTimeSupport


@pytest.mark.parametrize('runtime', ['process', 'thread'])
def test_runtime_pea_context(runtime):
    args = set_pea_parser().parse_args(['--runtime', runtime])
    with RunTimeSupport(args):
        pass
    RunTimeSupport(args).start().close()


def test_address_in_use():
    with pytest.raises(PeaFailToStart):
        args1 = set_pea_parser().parse_args(['--port-ctrl', '55555'])
        args2 = set_pea_parser().parse_args(['--port-ctrl', '55555'])
        with RunTimeSupport(args1), RunTimeSupport(args2):
            pass

    with pytest.raises(PeaFailToStart):
        args1 = set_pea_parser().parse_args(['--port-ctrl', '55555', '--runtime', 'thread'])
        args2 = set_pea_parser().parse_args(['--port-ctrl', '55555', '--runtime', 'thread'])
        with RunTimeSupport(args1), RunTimeSupport(args2):
            pass
