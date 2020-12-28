import pytest

from jina.excepts import RuntimeFailToStart
from jina.parser import set_pea_parser, set_gateway_parser
from jina.peapods.peas.base import BasePea
from jina.peapods.runtimes.asyncio.grpc import GRPCRuntime
from jina.peapods.runtimes.asyncio.rest import RESTRuntime
from jina.peapods.runtimes.base import BaseRuntime
from jina.peapods.runtimes.zed import ZEDRuntime


def test_base_runtime_fail_start():
    run_funcs = []
    class DummyRuntime(BaseRuntime):
        def setup(self):
            run_funcs.append('setup')
            raise NotImplementedError

        def teardown(self):
            run_funcs.append('teardown')
            raise NotImplementedError

        def run_forever(self):
            run_funcs.append('run_forever')
            raise NotImplementedError

        def cancel(self):
            run_funcs.append('cancel')
            raise NotImplementedError

    class Pea1(BasePea):
        runtime_cls = DummyRuntime

    arg = set_pea_parser().parse_args([])
    with pytest.raises(RuntimeFailToStart):
        with Pea1(arg):
            pass
    print(run_funcs)


def test_zed_runtime():
    class Pea1(BasePea):
        runtime_cls = ZEDRuntime

    arg = set_pea_parser().parse_args([])
    with Pea1(arg):
        pass


@pytest.mark.parametrize('cls', [GRPCRuntime, RESTRuntime])
def test_gateway_runtime(cls):
    class Pea1(BasePea):
        runtime_cls = cls

    arg = set_gateway_parser().parse_args([])
    with Pea1(arg):
        pass
