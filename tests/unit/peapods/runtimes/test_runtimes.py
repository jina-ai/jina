import multiprocessing
import os
import threading

import pytest

from jina.excepts import RuntimeFailToStart
from jina.parsers import set_pea_parser, set_gateway_parser
from jina.peapods import Pea
from jina.peapods.peas import BasePea
from jina.peapods.runtimes.gateway.grpc import GRPCRuntime
from jina.peapods.runtimes.gateway.websocket import WebSocketRuntime
from jina.peapods.runtimes.container import ContainerRuntime
from jina.peapods.runtimes.zmq.zed import ZEDRuntime


@pytest.mark.parametrize('runtime', ['thread', 'process'])
@pytest.mark.parametrize('ctrl_ipc', [True, False])
def test_zed_runtime(runtime, ctrl_ipc):
    class Pea1(BasePea):
        runtime_cls = ZEDRuntime

    arg = set_pea_parser().parse_args(
        ['--runtime-backend', runtime] + (['--ctrl-with-ipc'] if ctrl_ipc else [])
    )
    with Pea1(arg) as p:
        if runtime == 'thread':
            assert isinstance(p.worker, threading.Thread)
        elif runtime == 'process':
            assert isinstance(p.worker, multiprocessing.Process)


@pytest.mark.slow
@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='for unknown reason, this test is flaky on Github action, '
    'but locally it SHOULD work fine',
)
@pytest.mark.parametrize('cls', [GRPCRuntime, WebSocketRuntime])
@pytest.mark.parametrize('runtime', ['thread', 'process'])
def test_gateway_runtime(cls, runtime):
    class Pea1(BasePea):
        runtime_cls = cls

    arg = set_gateway_parser().parse_args(['--runtime-backend', runtime])
    with Pea1(arg):
        pass


@pytest.mark.parametrize('runtime', ['thread', 'process'])
def test_container_runtime_bad_entrypoint(runtime):
    class Pea1(BasePea):
        runtime_cls = ContainerRuntime

    # without correct entrypoint this will fail
    arg = set_pea_parser().parse_args(
        ['--uses', 'docker://jinaai/jina:test-pip', '--runtime-backend', runtime]
    )
    with pytest.raises(RuntimeFailToStart):
        with Pea1(arg):
            pass


@pytest.mark.parametrize('runtime', ['thread', 'process'])
def test_container_runtime_good_entrypoint(runtime):
    class Pea1(BasePea):
        runtime_cls = ContainerRuntime

    arg = set_pea_parser().parse_args(
        [
            '--uses',
            'docker://jinaai/jina:test-pip',
            '--entrypoint',
            'jina pod',
            '--runtime-backend',
            runtime,
        ]
    )
    with Pea1(arg):
        pass


@pytest.mark.parametrize('runtime', ['thread', 'process'])
def test_address_in_use(runtime):
    # test does not work with same control port, because right now the `READYNESS` signal is done by sending to that port
    p = ['--port-in', '55555', '--runtime-backend', runtime]
    args1 = set_pea_parser().parse_args(p)
    args2 = set_pea_parser().parse_args(p)
    with pytest.raises(RuntimeFailToStart):
        args1.name = 'Pea-1'
        args2.name = 'Pea-2'
        with Pea(args1), Pea(args2):
            pass


@pytest.mark.parametrize('runtime', ['thread', 'process'])
@pytest.mark.parametrize(
    'parser, args',
    [
        (
            set_pea_parser,
            ['--uses', 'docker://jinaai/jina:test-pip', '--entrypoint', 'jina pod'],
        ),
        (set_gateway_parser, ['--protocol', 'websocket']),
        (set_gateway_parser, ['--protocol', 'http']),
        (set_pea_parser, []),
    ],
)
def test_runtime_thread_process(runtime, parser, args):
    args.extend(['--runtime-backend', runtime])
    arg = parser().parse_args(args)
    with BasePea(arg):
        pass
