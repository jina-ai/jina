import multiprocessing
import threading

import pytest

from jina.excepts import RuntimeFailToStart
from jina.parsers import set_pea_parser, set_gateway_parser
from jina.peapods.peas.base import BasePea
from jina.peapods.runtimes.asyncio.grpc import GRPCRuntime
from jina.peapods.runtimes.asyncio.rest import RESTRuntime
from jina.peapods.runtimes.container import ContainerRuntime
from jina.peapods.runtimes.zmq.zed import ZEDRuntime


@pytest.mark.parametrize('runtime', ['thread', 'process'])
def test_zed_runtime(runtime):
    class Pea1(BasePea):
        runtime_cls = ZEDRuntime

    arg = set_pea_parser().parse_args(['--runtime-backend', runtime])
    with Pea1(arg) as p:
        if runtime == 'thread':
            assert isinstance(p, threading.Thread)
        elif runtime == 'process':
            assert isinstance(p, multiprocessing.Process)


@pytest.mark.parametrize('cls', [GRPCRuntime, RESTRuntime])
@pytest.mark.parametrize('runtime', ['thread', 'process'])
def test_gateway_runtime(cls, runtime):
    class Pea1(BasePea):
        runtime_cls = cls

    arg = set_gateway_parser().parse_args(['--runtime-backend', runtime])
    with Pea1(arg):
        pass


def test_container_runtime_bad_entrypoint():
    class Pea1(BasePea):
        runtime_cls = ContainerRuntime

    # without correct entrypoint this will fail
    arg = set_pea_parser().parse_args(['--uses', 'jinaai/jina:test-pip',
                                       ])
    with pytest.raises(RuntimeFailToStart):
        with Pea1(arg):
            pass


def test_container_runtime_good_entrypoint():
    class Pea1(BasePea):
        runtime_cls = ContainerRuntime

    # without correct entrypoint this will fail
    arg = set_pea_parser().parse_args(['--uses', 'jinaai/jina:test-pip',
                                       '--entrypoint', 'jina pod'])
    with Pea1(arg):
        pass


@pytest.mark.parametrize('runtime', ['thread', 'process'])
@pytest.mark.parametrize('cls, parser, args', [(ContainerRuntime, set_pea_parser,
                                                ['--uses', 'jinaai/jina:test-pip',
                                                 '--entrypoint', 'jina pod']),
                                               (RESTRuntime, set_gateway_parser, []),
                                               (ZEDRuntime, set_pea_parser, [])])
def test_runtime_thread_process(runtime, cls, parser, args):
    class Pea1(BasePea):
        runtime_cls = cls

    args.extend(['--runtime-backend', runtime])
    arg = parser().parse_args(args)
    with Pea1(arg):
        pass
