import multiprocessing
import time
from dataclasses import dataclass

import pytest

from jina import Executor, Flow, requests
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.worker import WorkerRuntime
from tests.helper import _generate_pod_args

from .test_runtimes import _create_gateway_runtime


class SlowExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        time.sleep(4)


def _create_worker_runtime(port, name=''):
    args = _generate_pod_args()
    args.port = port
    args.name = name
    if name == 'slow-executor':
        args.uses = 'SlowExecutor'

    with WorkerRuntime(args) as runtime:
        runtime.run_forever()


def _setup(worker_port, port, protocol, executor_name=''):
    graph_description = '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}'
    pod_addresses = f'{{"pod0": ["0.0.0.0:{worker_port}"]}}'

    # create a single worker runtime
    worker_process = multiprocessing.Process(
        target=_create_worker_runtime, args=(worker_port, executor_name)
    )
    worker_process.start()

    # create a single gateway runtime
    gateway_process = multiprocessing.Process(
        target=_create_gateway_runtime,
        args=(graph_description, pod_addresses, port, protocol),
    )
    gateway_process.start()

    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{worker_port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )
    AsyncNewLoopRuntime.wait_for_ready_or_shutdown(
        timeout=5.0,
        ctrl_address=f'0.0.0.0:{port}',
        ready_or_shutdown_event=multiprocessing.Event(),
    )
    return worker_process, gateway_process


@pytest.mark.asyncio
@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
async def test_gateway_warmup_fast_executor(port_generator, protocol, capfd):
    worker_port = port_generator()
    port = port_generator()
    worker_process, gateway_process = _setup(worker_port, port, protocol)

    time.sleep(1)

    gateway_process.terminate()
    gateway_process.join()
    worker_process.terminate()
    worker_process.join()

    assert gateway_process.exitcode == 0
    assert worker_process.exitcode == 0

    out, _ = capfd.readouterr()
    assert 'recv DataRequest at _jina_dry_run_' in out


@pytest.mark.asyncio
@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
async def test_gateway_warmup_slow_executor(port_generator, protocol, capfd):
    worker_port = port_generator()
    port = port_generator()
    worker_process, gateway_process = _setup(
        worker_port, port, protocol, 'slow-executor'
    )

    time.sleep(1)

    gateway_process.terminate()
    gateway_process.join()
    worker_process.terminate()
    worker_process.join()

    assert gateway_process.exitcode == 0
    assert worker_process.exitcode == 0

    out, _ = capfd.readouterr()
    assert 'recv DataRequest at _jina_dry_run_' in out
    assert 'ERROR' in out


@pytest.mark.asyncio
async def test_multi_protocol_gateway_fast_executor(port_generator, capfd):
    http_port = port_generator()
    grpc_port = port_generator()
    websocket_port = port_generator()
    flow = (
        Flow()
        .config_gateway(
            port=[http_port, grpc_port, websocket_port],
            protocol=['http', 'grpc', 'websocket'],
        )
        .add()
    )

    with flow:
        out, _ = capfd.readouterr()
        assert 'recv DataRequest at _jina_dry_run_' in out


@pytest.mark.asyncio
async def test_multi_protocol_gateway_slow_executor(port_generator, capfd):
    http_port = port_generator()
    grpc_port = port_generator()
    websocket_port = port_generator()
    flow = (
        Flow()
        .config_gateway(
            port=[http_port, grpc_port, websocket_port],
            protocol=['http', 'grpc', 'websocket'],
        )
        .add(uses='SlowExecutor', name='slowExecutor')
    )

    with flow:
        time.sleep(1)
        out, _ = capfd.readouterr()
        print(out)
        assert 'recv DataRequest at _jina_dry_run_' in out
